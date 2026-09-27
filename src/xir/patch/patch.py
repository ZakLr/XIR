"""Patch ops: add/remove/replace/modify/move/rename/deprecate across all node kinds."""
from __future__ import annotations
import re
from xir.ast.nodes import Experience, Entity, Capability, Surface, Flow, Meta

_LISTS = {"entity": "entities", "capability": "capabilities", "surface": "surfaces",
          "flow": "flows", "meta": "meta"}

def _list(exp: Experience, kind: str) -> list:
    return getattr(exp, _LISTS[kind])

def _find(exp: Experience, kind: str, name: str):
    for it in _list(exp, kind):
        key = it.text if kind == "meta" else it.name
        if key == name or getattr(it, "kind", "") + ":" + key == name:
            return it
    return None

def _build(kind: str, name: str, payload: dict):
    if kind == "entity":
        return Entity(name, payload.get("attrs", {}), payload.get("provenance", {}))
    if kind == "capability":
        return Capability(name, payload.get("input", {}), payload.get("output", ""),
            payload.get("requires", []), payload.get("effects", []),
            payload.get("confirmation", False), payload.get("audit", False),
            payload.get("provenance", {}))
    if kind == "surface":
        return Surface(name, payload.get("presents", ""), payload.get("components", []),
            payload.get("states", []), payload.get("provenance", {}))
    if kind == "flow":
        return Flow(name, payload.get("actor", ""), payload.get("steps", []),
            payload.get("provenance", {}))
    if kind == "meta":
        return Meta(payload.get("kind", "proposal"), name, payload.get("provenance", {}))
    raise ValueError(f"unknown kind {kind}")

def apply_patch(exp: Experience, op: str, kind: str, name: str, payload: dict | None = None) -> str:
    payload = dict(payload or {})
    if kind not in _LISTS:
        raise ValueError(f"unknown kind {kind}")
    items = _list(exp, kind)
    node = _find(exp, kind, name)
    if op == "add":
        if node is not None:
            raise ValueError(f"already exists: {kind}.{name}")
        items.append(_build(kind, name, payload))
        return f"added {kind}.{name}"
    if node is None:
        raise ValueError(f"not found: {kind}.{name}")
    if op == "remove":
        items.remove(node)
        return f"removed {kind}.{name}"
    if op == "rename":
        to = str(payload.get("to", name))
        if _find(exp, kind, to) is not None:
            raise ValueError(f"already exists: {kind}.{to}")
        if kind == "meta":
            node.text = to
        else:
            node.name = to
        return f"renamed {kind}.{name} -> {to}"
    if op == "replace":
        items[items.index(node)] = _build(kind, getattr(node, "name", name), payload)
        return f"replaced {kind}.{name}"
    if op == "modify":
        for k, v in payload.items():
            if k == "provenance":
                node.provenance = {**(node.provenance or {}), **v}
            elif hasattr(node, k):
                setattr(node, k, v)
            else:
                raise ValueError(f"unknown field {k} for {kind}")
        return f"modified {kind}.{name}"
    if op == "move":
        idx = items.index(node)
        to = int(payload.get("to", idx))
        items.insert(max(0, min(to, len(items) - 1)), items.pop(idx))
        return f"moved {kind}.{name} -> [{to}]"
    if op == "deprecate":
        node.provenance = {**(node.provenance or {}), "confidence": "deprecated"}
        return f"deprecated {kind}.{name}"
    raise ValueError(f"unknown op {op}")

_OP = re.compile(r'^\s*(add|remove|replace|modify|move|rename|deprecate)\s+(entity|capability|surface|flow|meta)\.(\w[\w\.\-]*)\s*$')

def apply_patch_text(exp: Experience, text: str) -> list[str]:
    """Minimal patch DSL: `op kind.name` lines with `field: value` payload lines."""
    out, cur = [], None
    body = text.strip()
    if body.startswith("patch"):
        body = body[body.index("{") + 1:body.rindex("}")]
    for line in body.splitlines():
        m = _OP.match(line)
        if m:
            if cur:
                out.append(apply_patch(exp, *cur))
            cur = (m.group(1), m.group(2), m.group(3).strip(), {})
        elif cur and ":" in line:
            k, v = line.split(":", 1)
            cur[3][k.strip()] = [x for x in re.findall(r"[\w\.\[\]|]+", v)] if k.strip() in ("states", "components", "steps", "requires") else v.strip()
    if cur:
        out.append(apply_patch(exp, *cur))
    return out
