"""Semantic query engine (§15, §16).

Operates on semantic graph relationships, not text matching. The keyword router
survives only as a thin convenience layer that resolves a phrase to an ID and
then defers to the graph.
"""
from __future__ import annotations
import re
from xir.ir.model import Model, Rel
from xir.semantic.graph import Graph

# phrase -> (kind, attribute) for the convenience router
_INTENT = [
    (r"\bpermissions?\b", "permission"),
    (r"\bevents?\b", "event"),
    (r"\bcapabilit(y|ies)\b", "capability"),
    (r"\binteraction", "interaction"),
    (r"\bcomponents?\b", "component"),
    (r"\bsurfaces?\b|\bscreens?\b", "surface"),
    (r"\bflows?\b", "flow"),
    (r"\bstates?\b", "state"),
    (r"\bgoals?\b", "goal"),
    (r"\bactors?\b", "actor"),
    (r"\b(entities|domain|models?)\b", "entity"),
]


def _label(rel: str) -> str:
    return rel.replace("-", " ").upper()


def _in(g: Graph, ref: str, kind: str) -> str | None:
    """Resolve preferring a given kind, so `createProject` means the capability when the
    question is about capabilities even if a goal shares the name."""
    bucket = g.model.bucket(kind)
    for i, n in bucket.items():
        if n.name == ref or n.name.lower() == ref.lower() or i.lower() == ref.lower():
            return i
        if i.split(".")[-1].lower() == ref.lower():
            return i
    return g.model.resolve(ref)


def _emit(g: Graph, id_: str, rels: list[str], title: str | None = None) -> list[str]:
    lines = [f"{title or g.kind(id_).upper()}: {g.name(id_)}  [{id_}]"]
    for r in rels:
        for t in g.out(id_, r):
            lines.append(f"  {_label(r)}: {g.name(t)}  [{t}]")
    return lines


_META_WORDS = ("requirement", "observation", "decision", "assumption", "inference", "proposal", "meta")


def show(g: Graph, ref: str) -> str:
    """`show <id-or-name>` — the node plus its asserted relationships.

    `show <kind>` with no specific node lists that bucket.
    """
    id_ = g.model.resolve(ref)
    if id_ is None:
        low = ref.lower().strip()
        if low in _META_WORDS:
            return "\n".join(f"{n.kind.upper()}: {n.claim} (confidence={n.confidence})  [{k}]"
                             for k, n in g.model.meta.items()) or f"no {low} in model"
        kind = _kind_from_query(ref)
        if kind:
            bucket = g.model.bucket(kind)
            if not bucket:
                return f"no {kind} in model"
            return "\n".join(f"{k.upper()}: {n.name}  [{k}]" for k, n in bucket.items())
        return f"unknown reference: {ref}"
    kind = g.kind(id_)
    default = {
        "capability": [Rel.REQUIRES, Rel.CONSUMES, Rel.PRODUCES, Rel.MUTATES, Rel.EMITS, Rel.CAUSES],
        "surface": [Rel.CONTAINS, Rel.PRESENTS, Rel.HAS_STATE],
        "component": [Rel.PRESENTS, Rel.INVOKES, Rel.HAS_STATE, Rel.CONTAINS, Rel.HAS_INTERACTION],
        "interaction": [Rel.INVOKES, Rel.HAS_INTERACTION],
        "flow": [Rel.STARTED_AT, Rel.ACHIEVES, "contains"],
        "machine": ["contains"],
        "state": [Rel.TRANSITIONS_TO],
        "entity": ["has"],
        "actor": [Rel.GRANTS],
        "goal": [Rel.ACHIEVED_BY],
        "permission": ["requires"],
        "event": [Rel.TRIGGERS],
    }.get(kind, [])
    lines = _emit(g, id_, default)
    back = g.reverse_rel("invokes")
    if back:
        for s in g.inc(id_, "invokes"):
            lines.append(f"  INVOKED BY: {g.name(s)}  [{s}]")
    if g.reverse_rel(Rel.HAS_INTERACTION):
        for s in g.inc(id_, Rel.HAS_INTERACTION):
            lines.append(f"  INTERACTION: {g.name(s)}  [{s}]")
    return "\n".join(lines)


def trace(g: Graph, ref: str) -> str:
    """`trace <capability>` — the full semantic slice an agent needs (§16)."""
    id_ = _in(g, ref, "capability")
    if id_ is None:
        return f"unknown reference: {ref}"
    m = g.model
    kind = g.kind(id_)
    if kind != "capability":
        return show(g, id_)
    node = m.get(id_)
    out = [f"CAPABILITY: {node.name}", f"  ID: {id_}"]
    if node.input:
        out.append("  INPUT: " + ", ".join(f"{k}: {v}" for k, v in node.input.items()))
    if node.output:
        out.append(f"  OUTPUT: {g.name(node.output)}  [{node.output}]")
    for r in node.requires:
        out.append(f"  REQUIRES: {g.name(r)}  [{r}]")
    for c in node.consumes:
        out.append(f"  CONSUMES: {g.name(c)}  [{c}]")
    for p in node.produces:
        out.append(f"  PRODUCES: {g.name(p)}  [{p}]")
    for f in node.mutates:
        out.append(f"  MUTATES: {g.name(f)}  [{f}]")
    for e in node.emits:
        out.append(f"  EMITS: {g.name(e)}  [{e}]")
    if node.confirmation:
        out.append("  CONFIRMATION: required")
    if node.audit:
        out.append("  AUDIT: required")
    # exposed-by: components that invoke it, then their surfaces
    for c in g.inc(id_, Rel.INVOKES):
        surfaces = g.inc(c, "contained-by")
        out.append(f"  EXPOSED BY: {g.name(c)}  [{c}]")
        for s in surfaces:
            out.append(f"    SURFACE: {g.name(s)}  [{s}]")
    for f in g.inc(Rel.ACHIEVES) if False else []:
        pass
    # flows that invoke or step to it
    for fk, f in m.flows.items():
        if fk == id_:
            continue
        hit = any(st.action == id_ or st.to == id_ for sk in f.steps if (st := m.steps.get(sk)))
        if hit or g.model.get(fk):
            out.append(f"  FLOW: {f.name}  [{fk}]")
    # states affected via caused transitions
    for t in g.out(id_, Rel.CAUSES):
        tr = m.transitions.get(t)
        if tr and tr.target:
            out.append(f"  STATE: {g.name(tr.target)}  [{tr.target}]")
    return "\n".join(out)


def follow(g: Graph, ref: str, rel: str, depth: int = 1) -> str:
    """`from <id> follow <relation>` — structural traversal (§15)."""
    id_ = g.model.resolve(ref)
    if id_ is None:
        return f"unknown reference: {ref}"
    seen = {id_}
    frontier = [id_]
    out: list[str] = []
    for _ in range(max(1, depth)):
        nxt = []
        for n in frontier:
            for t in g.out(n, rel):
                if t in seen:
                    continue
                seen.add(t)
                out.append(f"{g.kind(t).upper()}: {g.name(t)}  [{t}]")
                nxt.append(t)
        frontier = nxt
        if not frontier:
            break
    return "\n".join(out) or f"no {rel} edges from {id_}"


def who_can(g: Graph, capability_ref: str) -> str:
    """Actors that hold the permission a capability requires (§7)."""
    id_ = _in(g, capability_ref, "capability")
    if id_ is None:
        return f"unknown reference: {capability_ref}"
    node = g.model.get(id_)
    if node is None or not getattr(node, "requires", None):
        return f"{id_} requires no permission (available to all actors)"
    out = []
    for pid in node.requires:
        holders = [a for a in g.inc(pid, Rel.GRANTS)]
        if holders:
            out.append(f"{g.name(pid)}: " + ", ".join(g.name(h) for h in holders))
        else:
            out.append(f"{g.name(pid)}: NO ACTOR GRANTED (unreachable capability)")
    return "\n".join(out)


def affected(g: Graph, ref: str) -> str:
    """Everything that changes if this node changes (§19 regression support)."""
    id_ = g.model.resolve(ref) or _in(g, ref, "capability")
    if id_ is None:
        return f"unknown reference: {ref}"
    out = [f"AFFECTED BY {g.name(id_)} [{id_}]"]
    for rel in (Rel.INVOKES, Rel.REQUIRES, Rel.MUTATES, Rel.EMITS, Rel.CONSUMES, Rel.PRODUCES):
        for s in g.inc(id_, rel):
            out.append(f"  {rel}: {g.name(s)}  [{s}]")
    for s in g.inc(id_, "contained-by"):
        out.append(f"  contained-by: {g.name(s)}  [{s}]")
    for s in g.inc(id_, Rel.HAS_INTERACTION):
        out.append(f"  interaction: {g.name(s)}  [{s}]")
    return "\n".join(out)


def _kind_from_query(q: str) -> str | None:
    ql = q.lower()
    for pat, kind in _INTENT:
        if re.search(pat, ql):
            return kind
    return None


_STOP = {"who", "can", "which", "actor", "actors", "affected", "by", "impact",
         "what", "happens", "when", "user", "click", "clicks", "the", "a", "is",
         "does", "show", "trace", "from", "follow", "all", "callers", "of", "in",
         "to", "required", "state", "surface", "capability", "flow", "component",
         "event", "trigger", "triggers", "happen", "does", "get", "gets"}


def _named(q: str) -> str | None:
    """Pull a semantic reference out of a phrase: prefer a dotted ID, then a name."""
    m = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)\b", q)
    if m:
        return m.group(1)
    for w in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", q):
        if w.lower() not in _STOP:
            return w
    return None


def query(g: Graph, q: str) -> str:
    """Convenience router: resolve the phrase to an ID, then answer from the graph."""
    ql = q.lower().strip()
    if ql.startswith("trace "):
        return trace(g, q[6:].strip())
    if ql.startswith("show "):
        return show(g, q[5:].strip())
    m = re.match(r"from\s+(\S+)\s+follow\s+(\S+)", ql)
    if m:
        # IDs are case-sensitive, so recover them from the original query text
        raw = re.search(r"from\s+(\S+)\s+follow\s+(\S+)", q.strip(), re.I)
        return follow(g, raw.group(1) if raw else m.group(1), m.group(2))
    if "who can" in ql or "which actor" in ql or "unauthorized" in ql:
        return who_can(g, _named(q) or "")
    if "affected" in ql or "regression" in ql or "impact" in ql:
        return affected(g, _named(q) or "")
    if "what happens when" in ql or "click" in ql or "trigger" in ql:
        ref = _named(q)
        id_ = _in(g, ref, "interaction") if ref else None
        if id_:
            it = g.model.interactions[id_]
            if it.invokes:
                return trace(g, it.invokes)
            return show(g, id_)
        if ref:
            return trace(g, ref)
    kind = _kind_from_query(q)
    if kind:
        bucket = g.model.bucket(kind)
        if not bucket:
            return f"no {kind} in model"
        named = _named(q)
        if named and (_in(g, named, kind) or g.model.resolve(named)):
            return show(g, _in(g, named, kind) or g.model.resolve(named))
        return "\n".join(f"{k.upper()}: {n.name}  [{k}]" for k, n in bucket.items())
    if "state machine" in ql or "transition" in ql:
        return "\n".join(f"{k}: initial={n.initial} states={n.states}" for k, n in g.model.machines.items())
    if "invariant" in ql:
        return "\n".join(f"{k}: {n.rule}" for k, n in g.model.invariants.items()) or "no invariants"
    if "requirement" in ql or "decision" in ql or "inference" in ql:
        return "\n".join(f"{n.kind}: {n.claim} (confidence={n.confidence})" for n in g.model.meta.values()) or "no statements"
    if "requirement" in ql and not g.model.meta:
        return "no statements"
    return f"{g.model.name} [{g.model.id}]: {g.model.goal}"


def inspect(g: Graph, ref: str) -> str:
    return show(g, ref)


def explain(g: Graph, ref: str) -> str:
    return show(g, ref)
