"""Strict parser -> syntax AST. Raises on any invalid input (§21).

Earley, not LALR: the grammar has intentional overlap between legacy flat forms and
explicit blocks. LALR silently drops alternatives there. Earley also rejects embedded
transformers, so the tree is built first and transformed afterwards.

No silent tolerant fallback lives here. `parser/parse.py` owns that policy.
"""
from __future__ import annotations
from lark import Lark
from xir.ast import nodes as A


def _grammar() -> str:
    """Load the grammar from package data so it works installed, zipped or vendored."""
    try:
        from importlib.resources import files
        return (files("xir.parser") / "grammar.lark").read_text(encoding="utf-8")
    except Exception:
        from pathlib import Path
        return (Path(__file__).with_name("grammar.lark")).read_text(encoding="utf-8")


def _flat(items):
    for it in items:
        if isinstance(it, list):
            yield from _flat(it)
        else:
            yield it


def _kv(pairs) -> dict:
    out: dict = {}
    for p in pairs:
        if isinstance(p, tuple) and len(p) == 2:
            out[p[0]] = p[1]
    return out


def _prov(parts) -> A.Prov:
    d = dict(pairs for pairs in parts if isinstance(pairs, tuple))
    return A.Prov(source=d.get("source", ""), reference=d.get("reference", ""),
                  confidence=d.get("confidence", "unknown"))


_LIST_KEYS = ("actors", "goals", "permissions", "events", "components", "interactions",
              "machines", "invariants", "entities", "capabilities", "surfaces", "flows", "meta")


def _collect(nodes) -> dict:
    """Group (key, value) pairs into constructor kwargs, preserving declaration order."""
    out: dict = {}
    for p in nodes:
        if not (isinstance(p, tuple) and len(p) == 2):
            continue
        k, v = p
        if k in _LIST_KEYS:
            out.setdefault(k, []).extend(v if isinstance(v, list) else [v])
        else:
            out[k] = v
    return out


class _T:
    """Bottom-up transformer, equivalent to lark.Transformer but usable on an
    Earley tree (Earley forbids embedded transformers)."""

    def transform(self, tree):
        return self._visit(tree)

    def _visit(self, tree):
        from lark import Tree
        if isinstance(tree, Tree):
            kids = [self._visit(c) for c in tree.children]
            return getattr(self, tree.data)(kids)
        return tree

    # ---------- structure ----------
    def start(self, items):
        return items[0]

    def experience(self, items):
        return A.Experience(name=str(items[0]), **_collect(_flat(items[1:])))

    def exp_body(self, items):
        return list(_flat(items))

    def id_opt(self, items):
        return ("__id__", str(items[0]) if items else "")

    def decl_field(self, items):
        v = str(items[1]).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        return (str(items[0]), v)

    # ---------- statements ----------
    def goal_stmt(self, items):
        return ("goal", str(items[-1]).strip('"'))

    def version_stmt(self, items):
        return ("version", str(items[-1]))

    def actors_legacy(self, items):
        return ("actors", [A.Actor(name=str(i)) for i in items])

    def provenance_block(self, items):
        return ("provenance", _prov(_flat(items)))

    def prov_attr(self, items):
        return (str(items[0]), str(items[-1]).strip())

    # ---------- meta / evidence ----------
    def meta_decl(self, items):
        kind = str(items[0])
        body = items[1]
        if isinstance(body, tuple) and body[0] == "__simple__":
            return ("meta", A.Meta(kind=kind, name=kind, claim=body[1]))
        name, claim, conf, ev = "", "", "unknown", []
        if isinstance(body, tuple) and body[0] == "__named__":
            name, fields = body[1], body[2]
        elif isinstance(body, list):
            fields = body
        else:
            fields = []
        for p in fields:
            if not isinstance(p, tuple) or len(p) != 2:
                continue
            k, v = p
            if k == "claim":
                claim = str(v).strip('"')
            elif k == "confidence":
                conf = str(v)
            elif k == "evidence":
                ev = [str(x) for x in v]
            elif k == "__name__":
                name = str(v)
        return ("meta", A.Meta(kind=kind, name=name or kind, claim=claim,
                               confidence=conf, evidence=ev))

    def meta_simple_colon(self, items):
        return ("__simple__", str(items[0]).strip('"'))

    def meta_simple(self, items):
        return ("__simple__", str(items[0]).strip('"'))

    def meta_named(self, items):
        return ("__named__", str(items[0]), list(_flat(items[1:])))

    def meta_anon(self, items):
        return list(_flat(items))

    def meta_field(self, items):
        return items[0]

    def prov_claim(self, items):
        return ("claim", str(items[-1]).strip('"'))

    def prov_conf(self, items):
        return ("confidence", str(items[-1]))

    def prov_evid(self, items):
        return ("evidence", [str(i) for i in items])

    # ---------- goals ----------
    def goal_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("goals", A.Goal(name=str(items[0]), id=kw.pop("__id__", ""),
                                description=kw.pop("description", ""),
                                actor=kw.pop("actor", "")))

    def goal_id(self, items):
        return ("__id__", str(items[-1]))

    def goal_field(self, items):
        return items[0]

    # ---------- actors / permissions ----------
    def actor_block(self, items):
        return self.actor_flat(items)

    def actor_flat(self, items):
        parts = list(_flat(items[1:]))
        kw = _kv([p for p in parts if isinstance(p, tuple)])
        perms: list[str] = []
        for p in parts:
            if isinstance(p, tuple) and p[0] == "permissions":
                perms.extend(str(x) for x in p[1])
        return ("actors", A.Actor(name=str(items[0]), id=kw.pop("__id__", ""), permissions=perms))

    def actor_field(self, items):
        return items[0]

    def perm_block(self, items):
        return ("permissions", [str(i) for i in items])

    def perm_block_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("permissions", A.Permission(name=str(items[0]), id=kw.pop("__id__", ""),
                                            description=kw.pop("description", "")))

    def perm_flat(self, items):
        return self.perm_block_decl(items)

    def event_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("events", A.Event(name=str(items[0]), id=kw.pop("__id__", "")))

    # ---------- entities ----------
    def entity_decl(self, items):
        parts = list(_flat(items[1:]))
        attrs = [a for a in parts if isinstance(a, tuple) and a[0] not in ("__id__", "provenance")]
        kw = _kv(parts)
        return ("entities", A.Entity(name=str(items[0]), id=kw.pop("__id__", ""),
                                     attrs=dict(attrs), provenance=_prov(parts)))

    def ent_id(self, items):
        return ("__id__", str(items[-1]))

    def attr(self, items):
        return (str(items[0]), str(items[1]))

    def union_type(self, items):
        return " | ".join(str(i) for i in items)

    # ---------- capabilities ----------
    def capability_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("capabilities", A.Capability(
            name=str(items[0]), id=kw.pop("__id__", ""),
            input=kw.pop("input", {}), output=kw.pop("output", ""),
            requires=kw.pop("requires", []), consumes=kw.pop("consumes", []),
            produces=kw.pop("produces", []), mutates=kw.pop("mutates", []),
            emits=kw.pop("emits", []), effects=kw.pop("effects", []),
            confirmation=kw.pop("confirmation", False), audit=kw.pop("audit", False),
            provenance=_prov([p for p in _flat(items[1:]) if isinstance(p, tuple)])))

    def cap_id(self, items):
        return ("__id__", str(items[-1]))

    def cap_input(self, items):
        return ("input", dict(_flat(items)))

    def cap_output(self, items):
        return ("output", str(items[0]))

    def cap_requires(self, items):
        return ("requires", self._refs(items))

    def cap_consumes(self, items):
        return ("consumes", self._refs(items))

    def cap_produces(self, items):
        return ("produces", self._refs(items))

    def cap_mutates(self, items):
        return ("mutates", [str(i) for i in items])

    def cap_emits(self, items):
        return ("emits", self._refs(items))

    def cap_effects(self, items):
        # legacy free text; normalization upgrades it into structured `mutates` (§6)
        return ("effects", [str(items[0]).strip()])

    def cap_confirm(self, items):
        return ("confirmation", str(items[0]) in ("required", "true"))

    def cap_audit(self, items):
        return ("audit", str(items[0]) in ("required", "true"))

    def ref_list(self, items):
        return [str(i) for i in items]

    def _refs(self, items):
        out: list[str] = []
        for it in items:
            out.extend(str(x) for x in it) if isinstance(it, list) else out.append(str(it))
        return out

    # ---------- components ----------
    def component_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("components", A.Component(
            name=str(items[0]), id=kw.pop("__id__", ""),
            presents=kw.pop("presents", ""), invokes=kw.pop("invokes", []),
            states=kw.pop("states", []), children=kw.pop("contains", [])))

    def comp_id(self, items):
        return ("__id__", str(items[-1]))

    def comp_presents(self, items):
        return ("presents", str(items[0]))

    def comp_invokes(self, items):
        return items[0] if isinstance(items[0], tuple) else self.comp_invokes_flat(items)

    def comp_invokes_block(self, items):
        return ("invokes", [str(i) for i in items])

    def comp_invokes_flat(self, items):
        return ("invokes", [str(items[0])])

    def comp_states(self, items):
        return items[0] if isinstance(items[0], tuple) else self.comp_states_flat(items)

    def comp_states_block(self, items):
        return ("states", [str(i) for i in items])

    def comp_states_flat(self, items):
        return ("states", [str(items[0])])

    def comp_children(self, items):
        return items[0] if isinstance(items[0], tuple) else self.comp_children_flat(items)

    def comp_children_block(self, items):
        return ("contains", [str(i) for i in items])

    def comp_children_flat(self, items):
        return ("contains", [str(items[0])])

    # ---------- interactions ----------
    def interaction_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("interactions", A.Interaction(
            name=str(items[0]), id=kw.pop("__id__", ""),
            trigger=kw.pop("trigger", "click"), target=kw.pop("target", ""),
            invokes=kw.pop("invokes", "")))

    def int_id(self, items):
        return ("__id__", str(items[-1]))

    def int_trigger(self, items):
        return ("trigger", str(items[0]))

    def int_target(self, items):
        return ("target", str(items[0]))

    def int_invokes(self, items):
        return ("invokes", str(items[0]))

    # ---------- state machines ----------
    def machine_decl(self, items):
        parts = list(_flat(items[1:]))
        kw = _kv([p for p in parts if isinstance(p, tuple)])
        states = {p.name: p for p in parts if isinstance(p, A.StateDecl)}
        return ("machines", A.Machine(name=str(items[0]), id=kw.pop("__id__", ""),
                                      initial=kw.get("initial", ""), states=states))

    def m_id(self, items):
        return ("__id__", str(items[-1]))

    def m_initial(self, items):
        return ("initial", str(items[0]))

    def m_state(self, items):
        trs = [t for t in _flat(items[1:]) if isinstance(t, A.TransDecl)]
        return A.StateDecl(name=str(items[0]), transitions=trs)

    def trans(self, items):
        return items[0]

    def trans_on(self, items):
        kids = list(_flat(items))
        event, target, guard, action = "", "", "", ""
        for k in kids:
            if isinstance(k, str):
                if not event:
                    event = k
            elif isinstance(k, tuple):
                key, val = k
                if key == "target":
                    target = val
                elif key == "guard":
                    guard = val
                elif key == "action":
                    action = val
        return A.TransDecl(event=event, target=target, guard=guard, action=action)

    def trans_bare(self, items):
        return A.TransDecl(target=str(items[0]))

    def trans_target(self, items):
        return ("target", str(items[0]))

    def trans_guard(self, items):
        return ("guard", str(items[0]))

    def trans_action(self, items):
        return ("action", str(items[0]))

    # ---------- invariants ----------
    def invariant_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("invariants", A.Invariant(rule=kw.pop("rule", "") or str(items[0]),
                                          id=kw.pop("__id__", ""), scope=kw.pop("scope", "")))

    def inv_id(self, items):
        return ("__id__", str(items[-1]))

    # ---------- surfaces ----------
    def surface_decl(self, items):
        kw = _kv(_flat(items[1:]))
        return ("surfaces", A.Surface(
            name=str(items[0]), id=kw.pop("__id__", ""),
            presents=kw.pop("presents", ""), components=kw.pop("components", []),
            states=kw.pop("states", []), provenance=_prov([p for p in _flat(items[1:])
                                                            if isinstance(p, tuple)])))

    def surf_id(self, items):
        return ("__id__", str(items[-1]))

    def surf_presents(self, items):
        return ("presents", str(items[0]))

    def surf_comp(self, items):
        return items[0]

    def comp_block(self, items):
        return ("components", [str(i) for i in items])

    def layout_block(self, items):
        return ("components", [str(i) for i in items])

    def surf_states(self, items):
        return ("states", [str(i) for i in items])

    def surf_machine(self, items):
        return ("machine", str(items[0]))

    # ---------- flows ----------
    def flow_decl(self, items):
        parts = list(_flat(items[1:]))
        kw = _kv([p for p in parts if isinstance(p, tuple)])
        entry = kw.pop("entry", {})
        return ("flows", A.Flow(
            name=str(items[0]), id=kw.pop("__id__", ""),
            goal=kw.pop("goal", ""), actor=kw.pop("actor", ""),
            entry=entry.get("surface", "") if isinstance(entry, dict) else "",
            steps=[p for p in parts if isinstance(p, A.FlowStep)],
            branches=[p for p in parts if isinstance(p, A.FlowBranch)],
            provenance=_prov([p for p in parts if isinstance(p, tuple)])))

    def flow_id(self, items):
        return ("__id__", str(items[-1]))

    def flow_goal(self, items):
        return ("goal", str(items[0]))

    def flow_actor(self, items):
        return ("actor", str(items[0]))

    def flow_entry(self, items):
        return ("entry", dict(_flat(items)))

    def flow_step(self, items):
        f = _kv(_flat(items[1:]))
        return A.FlowStep(name=str(items[0]), id=f.pop("__id__", ""),
                          from_=f.pop("from", ""), action=f.pop("action", ""), to=f.pop("to", ""))

    def flow_step_ref(self, items):
        # legacy `step: surface.x`; a named step without a body
        return A.FlowStep(name=str(items[0]), to=str(items[0]))

    def flow_edge(self, items):
        # legacy `A -> B`; normalization turns it into an explicit step (§12, §31)
        return A.FlowStep(name=f"{str(items[0])}To{str(items[1])}",
                          from_=str(items[0]), to=str(items[1]))

    def flow_branch(self, items):
        cases, frm = [], ""
        for c in _flat(items[1:]):
            if isinstance(c, tuple) and len(c) == 2:
                if c[0] == "from":
                    frm = str(c[1])
                else:
                    cases.append((str(c[0]), str(c[1])))
        return A.FlowBranch(name=str(items[0]), cases=cases, from_=frm)

    def branch_from(self, items):
        return ("from", str(items[0]))

    def branch_case(self, items):
        return (str(items[0]), str(items[1]))


_parser = Lark(_grammar(), parser="earley", maybe_placeholders=False)


def parse_strict(text: str):
    return _T().transform(_parser.parse(text))
