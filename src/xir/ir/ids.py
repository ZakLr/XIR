"""Stable semantic identity (§4).

An ID is semantic identity and survives renames. A name is display/syntax only.
Canonical form: `<kind>.<camel-segment>.<camel-segment>...` (lowercased first letter).
IDs are validated against a strict pattern so a typo becomes a hard error, not a new node.
"""
from __future__ import annotations
import re

_ID_RE = re.compile(r"^(exp|goal|actor|permission|entity|field|capability|event|surface|component|interaction|machine|state|transition|flow|step|branch|invariant|meta|proposal|evidence)\.[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")

KINDS = (
    "exp", "goal", "actor", "permission", "entity", "field", "capability", "event",
    "surface", "component", "interaction", "machine", "state", "transition", "flow",
    "step", "branch", "invariant", "meta", "proposal", "evidence",
)

def _camel_one(s: str) -> str:
    if not s:
        return ""
    return s[:1].lower() + s[1:]


def camel(name: str) -> str:
    """Camel-case a name into one ID segment.

    Dots are significant and preserved: `project.archive` is already an ID-shaped
    name (permissions), so it must not collapse into `projectArchive`.
    """
    if "." in name:
        return ".".join(_camel_one(p) for p in name.split(".") if p)
    parts = re.split(r"[^A-Za-z0-9]+", name)
    segs = [p for p in parts if p]
    if not segs:
        return "unnamed"
    out = [_camel_one(segs[0])]
    for s in segs[1:]:
        out.append(s[:1].upper() + s[1:])
    return "".join(out)

def make_id(kind: str, *parts: str) -> str:
    """Build a canonical ID from a kind and name parts."""
    assert kind in KINDS, f"unknown kind {kind}"
    segs = [camel(p) for p in parts if p not in (None, "")]
    if not segs:
        segs = ["unnamed"]
    return f"{kind}." + ".".join(segs)

def valid_id(id_: str) -> bool:
    return bool(_ID_RE.match(id_))

def require_id(id_: str) -> str:
    if not valid_id(id_):
        raise ValueError(f"invalid semantic id: {id_!r}")
    return id_

def parent_id(id_: str) -> str:
    return id_.rsplit(".", 1)[0] if "." in id_ else id_

def kind_of(id_: str) -> str:
    return id_.split(".", 1)[0]
