"""AST -> semantic IR normalization (§3).

This module owns every identity and resolution decision. Nothing downstream
(graph, validation, query, patch, diff, compile) may read the syntax AST.
"""
from __future__ import annotations
import re
from xir.ast import nodes as A
from xir.ir import ids as I
from xir.ir.model import Model, Provenance, Rel

_PRIMITIVES = {"Text", "ID", "Int", "Bool", "Float", "String", "Date", "Enum"}


def _prov(p: A.Prov | None) -> Provenance:
    p = p or A.Prov()
    return Provenance(source=p.source or None, reference=p.reference or None,
                      confidence=p.confidence or "unknown", evidence=list(p.evidence or []))


def _strip_collection(v: str) -> str:
    """`Project[]` -> `Project`; keeps the type name resolvable."""
    return v.replace("[]", "").strip()


class Normalizer:
    def __init__(self, ast: A.Experience):
        self.ast = ast
        self.m = Model(id=A.Experience and (ast.id or I.make_id("exp", ast.name)),
                       name=ast.name, goal=ast.goal, version=ast.version)
        self._dangling: list[tuple[str, str, str]] = []  # (holder, relation, ref)
        self._unresolved: list[str] = []

    # ---------- helpers ----------
    def _id(self, kind: str, *parts: str) -> str:
        return I.make_id(kind, *parts)

    def _resolve(self, ref: str, kinds: tuple[str, ...], holder: str, rel: str,
                 strict: bool = True) -> str | None:
        """Resolve a written reference to a canonical ID, recording unresolved ones.

        `strict=False` is used for legacy loose forms (a bare `A -> B` flow edge), whose
        endpoints are positional hints rather than typed references; failing to resolve
        one of those is normal and must not be reported as a broken reference.
        """
        if not ref:
            return None
        r = ref.strip()
        # exact written ID
        if I.valid_id(r):
            return r
        hits = []
        for k in kinds:
            bucket = self.m.bucket(k)
            for i in bucket:
                if bucket[i].name == r:
                    hits.append(i)
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return None
        low = r.lower()
        for k in kinds:
            bucket = self.m.bucket(k)
            for i in bucket:
                if bucket[i].name.lower() == low or i.split(".")[-1].lower() == low:
                    hits.append(i)
        if len(hits) == 1:
            return hits[0]
        # path form, e.g. `Project.status` -> `field.project.status` (§6 mutations)
        path_hits = []
        for k in kinds:
            for i in self.m.bucket(k):
                if i.lower() == f"{k}.{low}" or i.lower().endswith(f".{low}"):
                    path_hits.append(i)
        if len(path_hits) == 1:
            return path_hits[0]
        if strict:
            self._dangling.append((holder, rel, r))
        return None

    # ---------- passes (order matters: refs must exist before referencing) ----------
    def run(self) -> Model:
        # order matters: a pass may only reference what an earlier pass has created
        self._meta()
        self._permissions()
        self._actors()      # references permissions
        self._goals()       # references actors
        self._entities()
        self._events()
        self._capabilities()  # references permissions, entities, fields, events
        self._machines()      # state names are machine-scoped
        self._components()    # references entities, capabilities, machines
        self._interactions()  # references components, capabilities
        self._surfaces()      # references entities, components, machines
        self._flows()         # references goals, actors, surfaces, states, interactions
        self._invariants()
        self.m.unresolved = [{"holder": h, "relation": r, "ref": x}
                             for h, r, x in self._dangling]
        return self.m

    def _meta(self):
        from xir.ir.model import Meta as M
        for x in self.ast.meta:
            mid = x.id or self._id("meta", x.kind, x.name or (x.claim[:24] or "note"))
            self.m.meta[mid] = M(id=mid, name=x.name or x.kind, kind=x.kind,
                                 claim=x.claim, confidence=x.confidence or "unknown",
                                 evidence=list(x.evidence or []))

    def _goals(self):
        from xir.ir.model import Goal as G
        for g in self.ast.goals:
            gid = g.id or self._id("goal", g.name)
            node = G(id=gid, name=g.name, description=g.description)
            if g.actor:
                node.actor = self._resolve(g.actor, ("actor",), gid, Rel.ACHIEVED_BY)
            self.m.goals[gid] = node

    def _permissions(self):
        from xir.ir.model import Permission as P
        for p in self.ast.permissions:
            pid = p.id or self._id("permission", p.name)
            self.m.permissions[pid] = P(id=pid, name=p.name, description=p.description)

    def _actors(self):
        from xir.ir.model import Actor as A_
        for a in self.ast.actors:
            aid = a.id or self._id("actor", a.name)
            perms = []
            for r in a.permissions:
                rp = self._resolve(r, ("permission",), aid, Rel.GRANTS)
                if rp:
                    perms.append(rp)
            self.m.actors[aid] = A_(id=aid, name=a.name, permissions=perms)

    def _entities(self):
        from xir.ir.model import Entity as E, Field_ as F
        for e in self.ast.entities:
            eid = e.id or self._id("entity", e.name)
            node = E(id=eid, name=e.name, provenance=_prov(e.provenance))
            self.m.entities[eid] = node
            for aname, atype in (e.attrs or {}).items():
                fid = self._id("field", e.name, aname)
                self.m.fields[fid] = F(id=fid, name=aname, type=atype)
                node.fields.append(fid)

    def _events(self):
        from xir.ir.model import Event as E
        for e in self.ast.events:
            eid = e.id or self._id("event", e.name)
            self.m.events[eid] = E(id=eid, name=e.name)

    def _capabilities(self):
        from xir.ir.model import Capability as C
        for c in self.ast.capabilities:
            cid = c.id or self._id("capability", c.name)
            node = C(id=cid, name=c.name, provenance=_prov(c.provenance),
                     confirmation=bool(c.confirmation), audit=bool(c.audit))
            node.input = dict(c.input or {})
            if c.output:
                node.output = self._resolve(c.output, ("entity",), cid, Rel.PRODUCES)
            for r in c.requires:
                v = self._resolve(r, ("permission",), cid, Rel.REQUIRES)
                if v:
                    node.requires.append(v)
            for r in c.consumes:
                v = self._resolve(r, ("entity",), cid, Rel.CONSUMES)
                if v:
                    node.consumes.append(v)
            for r in c.produces:
                v = self._resolve(r, ("entity",), cid, Rel.PRODUCES)
                if v:
                    node.produces.append(v)
            for r in c.mutates:
                v = self._resolve(r, ("field", "entity"), cid, Rel.MUTATES)
                if v:
                    node.mutates.append(v)
            for r in c.emits:
                v = self._resolve(r, ("event",), cid, Rel.EMITS)
                if v:
                    node.emits.append(v)
            # legacy `effects: project.status = archived` -> structured mutation (§6)
            for eff in (c.effects or []):
                for fid in _parse_effects(eff, self.m, cid):
                    if fid not in node.mutates:
                        node.mutates.append(fid)
            if node.output and node.output not in node.produces:
                node.produces.append(node.output)
            self.m.capabilities[cid] = node

    def _machines(self):
        from xir.ir.model import Machine as M, State as S, Transition as T
        for mch in self.ast.machines:
            mid = mch.id or self._id("machine", mch.name)
            node = M(id=mid, name=mch.name)
            local: dict[str, str] = {}
            for sname, sdecl in (mch.states or {}).items():
                sid = self._id("state", mch.name, sdecl.name)
                self.m.states[sid] = S(id=sid, name=sdecl.name)
                node.states.append(sid)
                local[sdecl.name.lower()] = sid
                local[sid.lower()] = sid
            if mch.initial:
                node.initial = local.get(str(mch.initial).strip().lower())
                node.initial_declared = bool(node.initial)
                if not node.initial:
                    self._dangling.append((mid, Rel.HAS_STATE, mch.initial))
            elif node.states:
                node.initial = node.states[0]  # inferred, not declared
            for sname, sdecl in (mch.states or {}).items():
                src = self._id("state", mch.name, sdecl.name)
                for t in sdecl.transitions:
                    tid = self._id("transition", mch.name, sdecl.name, t.event or t.target or "next")
                    # state names are machine-scoped: `error` in two machines is not ambiguous
                    tgt = local.get(str(t.target).strip().lower()) if t.target else None
                    if t.target and not tgt:
                        self._dangling.append((mid, Rel.TRANSITIONS_TO, t.target))
                    tr = T(id=tid, name=t.event or t.target or "next", source=src,
                           event=t.event, target=tgt or "", guard=t.guard or None,
                           action=t.action or None)
                    self.m.transitions[tid] = tr
                    node.transitions.append(tid)
            self.m.machines[mid] = node

    def _components(self):
        from xir.ir.model import Component as C
        for c in self.ast.components:
            cid = c.id or self._id("component", c.name)
            node = C(id=cid, name=c.name)
            if c.presents:
                node.presents = self._resolve(c.presents, ("entity",), cid, Rel.PRESENTS)
            for r in c.invokes:
                v = self._resolve(r, ("capability",), cid, Rel.INVOKES)
                if v:
                    node.invokes.append(v)
            for s in c.states:
                v = self._resolve(s, ("machine",), cid, Rel.HAS_STATE)
                if v:
                    node.states.append(v)
            for ch in c.children:
                v = self._resolve(ch, ("component",), cid, Rel.CONTAINS)
                if v:
                    node.children.append(v)
            self.m.components[cid] = node
        # legacy `components { Sidebar Main }` inside a surface -> synthetic components (§31)
        declared = {c.name.lower() for c in self.m.components.values()}
        for s in self.ast.surfaces:
            for cname in (s.components or []):
                if cname.lower() in declared:
                    continue  # a real component of this name already exists
                cid = self._id("component", s.name, cname)
                if cid not in self.m.components:
                    c = C(id=cid, name=cname)
                    c.legacy = True
                    self.m.components[cid] = c
                    declared.add(cname.lower())

    def _interactions(self):
        from xir.ir.model import Interaction as I_
        for it in self.ast.interactions:
            iid = it.id or self._id("interaction", it.name)
            node = I_(id=iid, name=it.name, trigger=it.trigger or "click")
            if it.target:
                node.target = self._resolve(it.target, ("component",), iid, Rel.HAS_INTERACTION)
            if it.invokes:
                node.invokes = self._resolve(it.invokes, ("capability",), iid, Rel.INVOKES)
            self.m.interactions[iid] = node

    def _surfaces(self):
        from xir.ir.model import Surface as S
        for s in self.ast.surfaces:
            sid = s.id or self._id("surface", s.name)
            node = S(id=sid, name=s.name, provenance=_prov(s.provenance))
            if s.presents:
                node.presents = self._resolve(_strip_collection(s.presents), ("entity",), sid, Rel.PRESENTS)
            for cname in (s.components or []):
                v = self._resolve(cname, ("component",), sid, Rel.CONTAINS) or self._id("component", s.name, cname)
                if v not in node.components:
                    node.components.append(v)
            for mk in (getattr(s, "machine", "") or "").split():
                v = self._resolve(mk, ("machine",), sid, Rel.HAS_STATE)
                if v and v not in node.states:
                    node.states.append(v)
            if s.states and not node.states:
                mid = self._id("machine", s.name, s.name)
                if mid not in self.m.machines:
                    from xir.ir.model import Machine as M, State as S_, Transition as T_
                    mnode = M(id=mid, name=f"{s.name} states")
                    for st in s.states:
                        stid = self._id("state", s.name, st)
                        self.m.states[stid] = S_(id=stid, name=st)
                        mnode.states.append(stid)
                    mnode.initial = mnode.states[0] if mnode.states else None
                    # a bare list of states declares no initial state and no transitions
                    mnode.initial_declared = False
                    # legacy states are names only; no transitions are invented
                    self.m.machines[mid] = mnode
                    node.states.append(mid)
            self.m.surfaces[sid] = node
            for c in node.components:
                if c in self.m.components and sid not in self.m.components[c].children:
                    pass  # containment direction is surface->component, set in graph

    def _flows(self):
        from xir.ir.model import Flow as F, Step as S, Branch as B
        for f in self.ast.flows:
            fid = f.id or self._id("flow", f.name)
            node = F(id=fid, name=f.name, provenance=_prov(f.provenance))
            if f.goal:
                node.goal = self._resolve(f.goal, ("goal",), fid, Rel.ACHIEVES)
            if f.actor:
                node.actor = self._resolve(f.actor, ("actor",), fid, Rel.STEPPED_AS)
            if f.entry:
                node.entry = self._resolve(f.entry, ("surface",), fid, Rel.STARTED_AT)
            for i, s in enumerate(f.steps or []):
                sid = s.id or self._id("step", f.name, s.name or f"step{i}")
                st = S(id=sid, name=s.name or f"step{i}")
                # a legacy bare edge (`A -> B`) has no declared action, so its endpoints
                # are hints: resolve what exists, do not report the rest as broken
                loose = not s.action
                if s.from_:
                    st.from_ = self._resolve(s.from_, ("surface", "state", "component", "entity"),
                                             sid, Rel.LEADS_TO, strict=not loose)
                if s.action:
                    st.action = self._resolve(s.action, ("interaction", "capability"), sid, Rel.INVOKES)
                if s.to:
                    st.to = self._resolve(s.to, ("surface", "state", "entity"),
                                          sid, Rel.LEADS_TO, strict=not loose)
                self.m.steps[sid] = st
                node.steps.append(sid)
            for b in (f.branches or []):
                bid = b.id or self._id("branch", f.name, b.name)
                bn = B(id=bid, name=b.name)
                if b.from_:
                    bn.from_ = self._resolve(b.from_, ("surface", "state", "entity"), bid, Rel.BRANCHED_FROM)
                for guard, target in (b.cases or []):
                    tg = self._resolve(target, ("surface", "state", "entity"), bid, Rel.LEADS_TO)
                    if tg:
                        bn.cases.append((guard, tg))
                self.m.branches[bid] = bn
                node.branches.append(bid)
            self.m.flows[fid] = node

    def _invariants(self):
        from xir.ir.model import Invariant as I_
        for i in self.ast.invariants:
            iid = i.id or self._id("invariant", i.rule[:32] or "rule")
            node = I_(id=iid, name=i.rule[:32], rule=i.rule)
            if i.scope:
                node.scope = self._resolve(i.scope, ("surface", "capability", "flow", "entity"), iid, Rel.GOVERNED_BY)
            self.m.invariants[iid] = node


def _parse_effects(text: str, m: Model, holder: str) -> list[str]:
    """`project.status = archived` -> [`field.project.status`]. Upgrades legacy free text."""
    out = []
    for part in re.split(r"[;,]", text):
        part = part.strip()
        if not part:
            continue
        lhs = re.split(r"[=]", part)[0].strip()
        segs = [s for s in re.split(r"[.\s]+", lhs) if s]
        if len(segs) >= 2:
            ent, attr = segs[0], segs[1]
            for eid, e in m.entities.items():
                if e.name.lower() == ent.lower():
                    for fid in e.fields:
                        if m.fields[fid].name.lower() == attr.lower():
                            out.append(fid)
    return out


def normalize(ast: A.Experience) -> Model:
    n = Normalizer(ast)
    model = n.run()
    return model
