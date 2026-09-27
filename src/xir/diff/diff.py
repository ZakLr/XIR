"""Semantic diff (§18). Identity-based, and rename-aware.

A rename is reported as RENAMED, not as remove+add, because IDs are semantic
identity: the same ID with a different name is the same thing renamed.
"""
from __future__ import annotations
from xir.ir.ids import kind_of
from xir.ir.model import Model

# fields compared per kind when deciding whether a same-ID node "changed"
_FIELDS = {
    "capability": ("input", "output", "requires", "consumes", "produces", "mutates",
                   "emits", "confirmation", "audit"),
    "surface": ("presents", "components", "states"),
    "component": ("presents", "invokes", "states", "children"),
    "interaction": ("trigger", "target", "invokes"),
    "flow": ("goal", "actor", "entry", "steps", "branches"),
    "entity": ("fields",),
    "actor": ("permissions",),
    "goal": ("description", "actor"),
    "machine": ("initial", "states", "transitions"),
    "transition": ("source", "event", "target", "guard", "action"),
    "step": ("from_", "action", "to"),
    "branch": ("from_", "cases"),
    "permission": ("description",),
    "invariant": ("rule", "scope"),
    "meta": ("kind", "claim", "confidence", "evidence"),
    "state": (),
    "field": ("type",),
    "event": (),
}


def _buckets(m: Model) -> dict[str, dict]:
    return m.buckets()


def _fmt(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {x}" for k, x in v.items()) + "}"
    return str(v)


def _node_of(m: Model, id_: str):
    return m.get(id_)


def diff(old: Model, new: Model) -> str:
    lines: list[str] = []
    if (old.version or "") != (new.version or ""):
        lines.append(f"CHANGED version: {old.version or '-'} -> {new.version or '-'}")

    ob, nb = _buckets(old), _buckets(new)
    for kind in ob:
        o, n = ob[kind], nb.get(kind, {})
        for id_ in sorted(set(n) - set(o)):
            lines.append(f"ADDED {kind}.{n[id_].name}: {id_}")
        for id_ in sorted(set(o) - set(n)):
            lines.append(f"REMOVED {kind}.{o[id_].name}: {id_}")
        for id_ in sorted(set(o) & set(n)):
            a, b = o[id_], n[id_]
            if a.name != b.name:
                lines.append(f"RENAMED {kind}.{a.name} -> {kind}.{b.name}: {id_}")
            for f in _FIELDS.get(kind, ()):
                av, bv = getattr(a, f, None), getattr(b, f, None)
                if av != bv:
                    lines.append(f"CHANGED {kind}.{b.name} ({id_})")
                    lines.append(f"    {f}:")
                    lines.append(f"        {_fmt(av)}")
                    lines.append(f"        -> {_fmt(bv)}")
    return "\n".join(lines) or "no semantic changes"


def changed_ids(old: Model, new: Model) -> set[str]:
    """Machine-readable companion to `diff`."""
    out: set[str] = set()
    ob, nb = _buckets(old), _buckets(new)
    for kind in ob:
        o, n = ob[kind], nb.get(kind, {})
        out |= set(o) ^ set(n)
        for id_ in set(o) & set(n):
            if any(getattr(o[id_], f, None) != getattr(n[id_], f, None)
                   for f in _FIELDS.get(kind, ())):
                out.add(id_)
    return out
