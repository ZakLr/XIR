"""Semantic validation (§19). Runs on the IR, never on the syntax AST.

Every finding is `(code, message, subject_id)` so callers can report a stable code
and the exact node that caused it.
"""
from __future__ import annotations
from xir.ir.ids import valid_id, kind_of
from xir.ir.model import Model, Rel, CONFIDENCE, SOURCES
from xir.semantic.graph import Graph

_PRIMITIVES = {"Text", "ID", "Int", "Bool", "Float", "String", "Date", "Enum", "Time"}
_DESTRUCTIVE = ("delete", "destroy", "archive", "remove", "purge", "revoke")


class Finding(tuple):
    def __new__(cls, code: str, message: str, subject: str = ""):
        return super().__new__(cls, (code, message, subject))

    @property
    def code(self) -> str:
        return self[0]

    @property
    def message(self) -> str:
        return self[1]

    @property
    def subject(self) -> str:
        return self[2]

    def __str__(self) -> str:
        return f"{self[0]}: {self[1]}" + (f" [{self[2]}]" if self[2] else "")


def _exists(m: Model, id_: str | None) -> bool:
    return bool(id_) and m.get(id_) is not None


def validate(m: Model) -> list[Finding]:
    g = Graph(m)
    out: list[Finding] = []
    out += _identity(m)
    out += _capabilities(m)
    out += _components(m, g)
    out += _interactions(m, g)
    out += _machines(m)
    out += _flows(m, g)
    out += _security(m, g)
    out += _evidence(m)
    return out


# ---------- identity ----------
def _identity(m: Model) -> list[Finding]:
    out: list[Finding] = []
    for u in getattr(m, "unresolved", []):
        out.append(Finding("UNRESOLVED_REFERENCE",
                           f"{u['holder']} has an unresolved {u['relation']} reference {u['ref']!r}",
                           u["holder"]))
    seen: set[str] = set()
    for id_ in m.all_ids():
        if id_ in seen:
            out.append(Finding("DUPLICATE_ID", f"duplicate semantic id {id_}", id_))
        seen.add(id_)
        if not valid_id(id_):
            out.append(Finding("INVALID_ID", f"malformed semantic id {id_!r}", id_))
    for id_ in m.all_ids():
        node = m.get(id_)
        if node is None or node is m:
            continue
        for rel, targets in _refs(node):
            for t in targets:
                if not _exists(m, t):
                    out.append(Finding("DANGLING_REFERENCE",
                                      f"{kind_of(id_)}.{node.name} {rel} -> unknown {t!r}", id_))
    return out


def _refs(node) -> list[tuple[str, list[str]]]:
    """Typed reference sweep. `target` means different things per node kind, so it is
    handled explicitly rather than lumped in with the generic attributes."""
    pairs: list[tuple[str, list[str]]] = []
    generic = (("requires", Rel.REQUIRES), ("consumes", Rel.CONSUMES),
               ("produces", Rel.PRODUCES), ("mutates", Rel.MUTATES),
               ("emits", Rel.EMITS), ("invokes", Rel.INVOKES),
               ("presents", Rel.PRESENTS), ("states", Rel.HAS_STATE),
               ("children", Rel.CONTAINS), ("components", Rel.CONTAINS),
               ("actor", "actor"), ("goal", Rel.ACHIEVES), ("entry", Rel.STARTED_AT),
               ("from_", Rel.LEADS_TO), ("action", Rel.INVOKES), ("to", Rel.LEADS_TO),
               ("permissions", Rel.GRANTS), ("fields", "has"), ("initial", "initial"),
               ("source", "from"), ("scope", Rel.GOVERNED_BY))
    for attr, rel in generic:
        val = getattr(node, attr, None)
        if val is None or isinstance(val, bool):
            continue
        pairs.append((rel, [val] if isinstance(val, str) else list(val)))
    kind = type(node).__name__
    if kind == "Interaction" and getattr(node, "target", None):
        pairs.append((Rel.HAS_INTERACTION, [node.target]))
    if kind == "Transition":
        if getattr(node, "source", None):
            pairs.append(("from-state", [node.source]))
        if getattr(node, "target", None):
            pairs.append((Rel.TRANSITIONS_TO, [node.target]))
    return pairs


# ---------- capabilities ----------
def _capabilities(m: Model) -> list[Finding]:
    out: list[Finding] = []
    for cid, c in m.capabilities.items():
        if not c.input and not c.output and not c.mutates and not c.emits:
            out.append(Finding("INVALID_CAPABILITY",
                               f"capability {c.name} declares no input, output, mutation or event", cid))
        for pname, t in c.input.items():
            for alt in t.split("|"):
                base = alt.strip().split("[")[0].strip()
                if base and base not in _PRIMITIVES and m.resolve(base) is None:
                    out.append(Finding("INVALID_INPUT_TYPE",
                                       f"capability {c.name} input {pname}: unknown type {base!r}", cid))
        if c.output and not _exists(m, c.output):
            out.append(Finding("INVALID_OUTPUT_REF", f"capability {c.name} output unknown", cid))
        for f in c.mutates:
            if m.get(f) is None or kind_of(f) != "field":
                out.append(Finding("INVALID_MUTATION",
                                   f"capability {c.name} mutates {f!r} which is not a known field", cid))
        for e in c.emits:
            if not _exists(m, e):
                out.append(Finding("INVALID_EVENT", f"capability {c.name} emits unknown {e!r}", cid))
        if any(k in c.name.lower() for k in _DESTRUCTIVE) and not c.confirmation:
            out.append(Finding("MISSING_CONFIRMATION",
                               f"destructive capability {c.name} requires confirmation", cid))
    return out


# ---------- components / interactions ----------
def _components(m: Model, g: Graph) -> list[Finding]:
    out: list[Finding] = []
    for cid, c in m.components.items():
        if not (c.invokes or c.presents or c.children or c.states):
            if not getattr(c, "legacy", False):
                out.append(Finding("EMPTY_COMPONENT", f"component {c.name} has no semantics", cid))
        for inv in c.invokes:
            if not _exists(m, inv):
                out.append(Finding("INVALID_CAPABILITY_REF",
                                   f"component {c.name} invokes unknown {inv!r}", cid))
        for ch in c.children:
            if not _exists(m, ch):
                out.append(Finding("INVALID_CHILD_COMPONENT",
                                   f"component {c.name} contains unknown {ch!r}", cid))
        if not g.inc(cid, Rel.CONTAINS) and not g.inc(cid, Rel.HAS_INTERACTION):
            out.append(Finding("ORPHAN_COMPONENT",
                               f"component {c.name} is not placed on any surface", cid))
    return out


def _interactions(m: Model, g: Graph) -> list[Finding]:
    out: list[Finding] = []
    for iid, it in m.interactions.items():
        if not it.invokes:
            out.append(Finding("INTERACTION_WITHOUT_CAPABILITY",
                               f"interaction {it.name} invokes nothing", iid))
        elif not _exists(m, it.invokes):
            out.append(Finding("INVALID_CAPABILITY_REF",
                               f"interaction {it.name} invokes unknown {it.invokes!r}", iid))
        if it.target and not _exists(m, it.target):
            out.append(Finding("INVALID_TARGET_COMPONENT",
                               f"interaction {it.name} targets unknown {it.target!r}", iid))
    return out


# ---------- state machines ----------
def _machines(m: Model) -> list[Finding]:
    out: list[Finding] = []
    for mid, mc in m.machines.items():
        if not mc.states:
            out.append(Finding("EMPTY_MACHINE", f"state machine {mc.name} has no states", mid))
            continue
        if not mc.initial:
            out.append(Finding("MISSING_INITIAL_STATE",
                               f"state machine {mc.name} has no initial state", mid))
        elif not getattr(mc, "initial_declared", True) and mc.transitions:
            # an inferred initial state hides an authoring omission worth reporting
            out.append(Finding("MISSING_INITIAL_STATE",
                               f"state machine {mc.name} does not declare an initial state", mid))
        elif mc.initial not in mc.states:
            out.append(Finding("INVALID_INITIAL_STATE",
                               f"state machine {mc.name} initial {mc.initial} is not one of its states", mid))
        # reachability from the initial state
        adj: dict[str, list[str]] = {s: [] for s in mc.states}
        for tid in mc.transitions:
            t = m.transitions.get(tid)
            if not t:
                continue
            if t.source not in adj:
                adj[t.source] = []
            if t.target:
                adj[t.source].append(t.target)
        for tid in mc.transitions:
            t = m.transitions.get(tid)
            if t and t.target and t.target not in mc.states:
                out.append(Finding("INVALID_TRANSITION_TARGET",
                                   f"transition {t.name} targets {t.target} which is not a state of {mc.name}", tid))
        # A bare list of states (legacy form) has no transitions to check reachability with.
        if not mc.transitions:
            return out
        seen, stack = set(), ([mc.initial] if mc.initial in adj else [])
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(adj.get(cur, []))
        for s in mc.states:
            if s not in seen:
                out.append(Finding("UNREACHABLE_STATE",
                                   f"state {m.states[s].name if s in m.states else s} is unreachable from {mc.name}", s))
            elif not adj.get(s):
                out.append(Finding("DEAD_END_STATE",
                                   f"state {m.states[s].name if s in m.states else s} has no outgoing transition", s))
    return out


# ---------- flows ----------
def _flows(m: Model, g: Graph) -> list[Finding]:
    out: list[Finding] = []
    for fid, f in m.flows.items():
        if not (f.steps or f.branches):
            out.append(Finding("DEAD_END_FLOW", f"flow {f.name} has no steps or branches", fid))
        if f.actor and not _exists(m, f.actor):
            out.append(Finding("INVALID_ACTOR", f"flow {f.name} actor {f.actor!r} unknown", fid))
        if f.goal and not _exists(m, f.goal):
            out.append(Finding("INVALID_GOAL", f"flow {f.name} goal {f.goal!r} unknown", fid))
        if f.entry and not _exists(m, f.entry):
            out.append(Finding("INVALID_SURFACE", f"flow {f.name} entry {f.entry!r} unknown", fid))
        for sid in f.steps:
            st = m.steps.get(sid)
            if not st:
                out.append(Finding("INVALID_STEP", f"flow {f.name} references missing step {sid}", fid))
                continue
            if st.action and not _exists(m, st.action):
                out.append(Finding("INVALID_INTERACTION",
                                   f"flow {f.name} step {st.name} action {st.action!r} unknown", sid))
            if st.to and not _exists(m, st.to):
                out.append(Finding("UNREACHABLE_STEP",
                                   f"flow {f.name} step {st.name} goes to unknown {st.to!r}", sid))
        for bid in f.branches:
            b = m.branches.get(bid)
            if not b or not b.cases:
                out.append(Finding("BROKEN_BRANCH", f"flow {f.name} has an empty branch {bid}", fid))
                continue
            for guard, target in b.cases:
                if not _exists(m, target):
                    out.append(Finding("BROKEN_BRANCH",
                                       f"flow {f.name} branch {b.name} case {guard} -> unknown {target!r}", bid))
    return out


# ---------- security (§19) ----------
def _security(m: Model, g: Graph) -> list[Finding]:
    """actor -> interaction -> capability -> permission must be satisfiable."""
    out: list[Finding] = []
    for fid, f in m.flows.items():
        if not f.actor:
            continue
        actor = m.actors.get(f.actor)
        if actor is None:
            continue
        held = set(actor.permissions)
        actions: list[str] = []
        for sid in f.steps:
            st = m.steps.get(sid)
            if st and st.action:
                actions.append(st.action)
        for iid, it in m.interactions.items():
            if g.inc(iid, "contained-by") and f.actor and it.invokes:
                if any(it.invokes in [a for a in actions] or a == it.invokes for a in actions):
                    actions.append(it.invokes)
        for action in actions:
            cap = m.get(action)
            if cap is None or kind_of(action) != "capability":
                continue
            for pid in getattr(cap, "requires", []):
                if pid not in held:
                    out.append(Finding("UNAUTHORIZED_CAPABILITY",
                                       f"actor {actor.name} may reach {cap.name} but lacks {m.permissions[pid].name if pid in m.permissions else pid}",
                                       action))
    # a capability no actor may use is dead weight
    for cid, c in m.capabilities.items():
        if not c.requires:
            continue
        holders = [a for a in m.actors.values() if any(p in a.permissions for p in c.requires)]
        if m.actors and not holders:
            out.append(Finding("UNREACHABLE_CAPABILITY",
                               f"no actor holds the permission required by {c.name}", cid))
    return out


# ---------- evidence (§20) ----------
def _evidence(m: Model) -> list[Finding]:
    out: list[Finding] = []
    for mid, n in m.meta.items():
        if n.confidence not in CONFIDENCE:
            out.append(Finding("INVALID_CONFIDENCE",
                               f"{n.kind} {n.name}: unknown confidence {n.confidence!r}", mid))
        if n.kind == "inference" and n.confidence == "confirmed":
            out.append(Finding("UNSUPPORTED_CONFIDENCE",
                               f"inference {n.name} cannot claim confirmed", mid))
        if n.kind in ("requirement", "decision") and not n.claim:
            out.append(Finding("EMPTY_CLAIM", f"{n.kind} {n.name} has no claim", mid))
    for id_ in m.all_ids():
        node = m.get(id_)
        prov = getattr(node, "provenance", None)
        if prov is None or node is m:
            continue
        if prov.source and prov.source not in SOURCES:
            out.append(Finding("INVALID_PROVENANCE",
                               f"{kind_of(id_)}.{node.name} unknown source {prov.source!r}", id_))
        if prov.confidence not in CONFIDENCE:
            out.append(Finding("INVALID_CONFIDENCE",
                               f"{kind_of(id_)}.{node.name} unknown confidence {prov.confidence!r}", id_))
        if prov.source == "inference" and prov.confidence == "confirmed":
            out.append(Finding("UNSUPPORTED_CONFIDENCE",
                               f"{kind_of(id_)}.{node.name} inference cannot claim confirmed", id_))
    for inv in m.invariants.values():
        pass  # invariant scope is already covered by the generic reference sweep
    return out
