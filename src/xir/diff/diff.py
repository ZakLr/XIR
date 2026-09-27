"""Semantic diff on identity, not text."""
from __future__ import annotations
from xir.ast.nodes import Experience

def _names(items) -> set[str]:
    return {i.name for i in items}

def _provmap(items) -> dict[str, dict]:
    return {i.name: (i.provenance or {}) for i in items}

def diff(old: Experience, new: Experience) -> str:
    lines = []
    if (old.version or "") != (new.version or ""):
        lines.append(f"Changed version: {old.version or 'none'} -> {new.version or 'none'}")
    om = {(m.kind, m.text) for m in old.meta}
    nm = {(m.kind, m.text) for m in new.meta}
    for kind, text in sorted(nm - om):
        lines.append(f"Added {kind}: \"{text}\"")
    for kind, text in sorted(om - nm):
        lines.append(f"Removed {kind}: \"{text}\"")
    for kind in ("entities", "capabilities", "surfaces", "flows"):
        o, n = _names(getattr(old, kind)), _names(getattr(new, kind))
        label = "entitie" if kind == "entities" else kind.rstrip("s")
        for x in sorted(n - o):
            lines.append(f"Added {label}: {x}")
        for x in sorted(o - n):
            lines.append(f"Removed {kind}: {x}")
        op, np = _provmap(getattr(old, kind)), _provmap(getattr(new, kind))
        for x in sorted(set(op) & set(np)):
            if op[x] != np[x]:
                lines.append(f"Changed {label}.{x} provenance")
    # capability detail changes (input/output/requires/effects/confirmation)
    oc = {c.name: c for c in old.capabilities}
    nc = {c.name: c for c in new.capabilities}
    for x in sorted(set(oc) & set(nc)):
        a, b = oc[x], nc[x]
        if (a.input, a.output, a.requires, a.effects, a.confirmation, a.audit) != \
           (b.input, b.output, b.requires, b.effects, b.confirmation, b.audit):
            lines.append(f"Changed capability: {x}")
    return "\n".join(lines) or "no semantic changes"
