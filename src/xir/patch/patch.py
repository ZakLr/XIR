"""Atomic semantic patches (§17).

    PATCH -> resolve IDs -> apply -> rebuild -> validate -> commit | rollback

A patch never leaves the model partially invalid. Every op runs against a deep copy;
the caller's model is only replaced if validation passes (or if the patch is
explicitly allowed to be advisory).
"""
from __future__ import annotations
import copy
import re
from xir.ir import ids as I
from xir.ir.model import Model, Rel
from xir.validator.validate import validate

_REL_ATTRS = {
    Rel.REQUIRES: "requires", Rel.CONSUMES: "consumes", Rel.PRODUCES: "produces",
    Rel.MUTATES: "mutates", Rel.EMITS: "emits", Rel.INVOKES: "invokes",
    Rel.CONTAINS: "children", Rel.HAS_STATE: "states", Rel.HAS_INTERACTION: "interactions",
    Rel.GRANTS: "permissions", Rel.PRESENTS: "presents", Rel.ACHIEVES: "goal",
    Rel.STARTED_AT: "entry", Rel.TRANSITIONS_TO: "target", "from": "from_",
    Rel.LEADS_TO: "to", Rel.HAS: "children",
}


class PatchError(Exception):
    pass


class Transaction:
    """Apply ops atomically to a Model."""

    def __init__(self, model: Model, strict: bool = True):
        self.model = model
        self.strict = strict
        self.log: list[str] = []
        self._original = model.model_copy(deep=True)

    # ---------- helpers ----------
    def _resolve(self, ref: str) -> str:
        id_ = self.model.resolve(ref)
        if id_ is None:
            raise PatchError(f"unknown reference: {ref!r}")
        return id_

    def _bucket(self, kind: str) -> dict:
        return self.model.bucket(kind)

    def _refs_to(self, id_: str) -> list[tuple[str, str, str]]:
        """(holder_id, attr, value) for every reference pointing at id_."""
        out: list[tuple[str, str, str]] = []
        m = self.model
        for kind, bucket in m.buckets().items():
            for hid, node in bucket.items():
                for attr, rel in (("requires", Rel.REQUIRES), ("consumes", Rel.CONSUMES),
                                  ("produces", Rel.PRODUCES), ("mutates", Rel.MUTATES),
                                  ("emits", Rel.EMITS), ("invokes", Rel.INVOKES),
                                  ("presents", Rel.PRESENTS), ("states", Rel.HAS_STATE),
                                  ("children", Rel.CONTAINS), ("components", Rel.CONTAINS),
                                  ("permissions", Rel.GRANTS), ("fields", "has"),
                                  ("scope", Rel.GOVERNED_BY), ("source", "from"),
                                  ("target", None), ("to", None), ("action", None),
                                  ("entry", None), ("from_", None)):
                    if attr == "invokes_target":
                        val = getattr(node, "invokes", None)
                    else:
                        val = getattr(node, attr, None)
                    if val is None or isinstance(val, bool):
                        continue
                    vals = [val] if isinstance(val, str) else list(val)
                    if id_ in vals:
                        out.append((hid, attr, id_))
        return out

    # ---------- ops ----------
    def rename(self, ref: str, new_name: str, new_id: str | None = None) -> str:
        """Rename preserving semantic identity; all references follow automatically."""
        id_ = self._resolve(ref)
        kind = I.kind_of(id_)
        bucket = self._bucket(kind)
        node = bucket[id_]
        target = new_id or id_
        if new_id and new_id != id_:
            if new_id in bucket:
                raise PatchError(f"target id already exists: {new_id}")
            # references are stored as ids, so rewrite them to the new id
            for holder, attr, _ in self._refs_to(id_):
                h = self.model.get(holder)
                if h is None:
                    continue
                val = getattr(h, attr, None)
                if isinstance(val, str):
                    setattr(h, attr, new_id)
                elif isinstance(val, list):
                    setattr(h, attr, [new_id if x == id_ else x for x in val])
        node.name = new_name
        bucket.pop(id_)
        bucket[target] = node
        self.log.append(f"renamed {id_} -> {target} ({new_name})")
        return target

    def modify(self, ref: str, **fields) -> str:
        id_ = self._resolve(ref)
        node = self.model.get(id_)
        if node is None:
            raise PatchError(f"unknown reference: {ref!r}")
        for k, v in fields.items():
            if k == "states" and isinstance(v, str):
                v = [v]
            if k in _LIST_REF_FIELDS:
                v = [self._resolve(x) for x in v]
            elif k in _SCALAR_REF_FIELDS and isinstance(v, str) and v:
                v = self._resolve(v) or v
            if not hasattr(node, k):
                raise PatchError(f"{type(node).__name__} has no field {k!r}")
            setattr(node, k, v)
        self.log.append(f"modified {id_} ({', '.join(fields)})")
        return id_

    def add(self, kind: str, ref: str, **fields) -> str:
        from xir.ir import model as M
        cls = {"goal": M.Goal, "actor": M.Actor, "permission": M.Permission, "entity": M.Entity,
               "field": M.Field_, "event": M.Event, "capability": M.Capability,
               "surface": M.Surface, "component": M.Component, "interaction": M.Interaction,
               "machine": M.Machine, "state": M.State, "flow": M.Flow,
               "invariant": M.Invariant}.get(kind)
        if cls is None:
            raise PatchError(f"cannot add kind {kind!r}")
        # `add surface.Help` names a node, so the kind prefix is not part of the name
        name = ref.split(".", 1)[1] if ref.startswith(f"{kind}.") else ref
        id_ = fields.pop("id", "") or I.make_id(kind, name)
        if id_ in self._bucket(kind):
            raise PatchError(f"already exists: {id_}")
        if not I.valid_id(id_):
            raise PatchError(f"invalid id: {id_!r}")
        for k in list(fields):
            if k in ("requires", "consumes", "produces", "mutates", "emits", "invokes",
                     "children", "components", "permissions", "presents", "states"):
                v = fields[k]
                fields[k] = [self._resolve(x) if not I.valid_id(x) else x
                             for x in (v if isinstance(v, list) else [v])]
        self._bucket(kind)[id_] = cls(id=id_, name=name, **fields)
        self.log.append(f"added {kind}.{name}: {id_}")
        return id_

    def remove(self, ref: str) -> str:
        id_ = self._resolve(ref)
        kind = I.kind_of(id_)
        dependents = self._refs_to(id_)
        if dependents and self.strict:
            raise PatchError(
                f"cannot remove {id_}: still referenced by "
                + ", ".join(f"{h}.{a}" for h, a, _ in dependents))
        if dependents:
            for holder, attr, _ in dependents:
                h = self.model.get(holder)
                if h is None:
                    continue
                val = getattr(h, attr, None)
                if isinstance(val, list):
                    setattr(h, attr, [x for x in val if x != id_])
                else:
                    setattr(h, attr, None)
        self.model.remove(id_)
        self.log.append(f"removed {id_}")
        return id_

    def deprecate(self, ref: str) -> str:
        from xir.ir.model import Provenance
        id_ = self._resolve(ref)
        node = self.model.get(id_)
        if node is None:
            raise PatchError(f"unknown reference: {ref!r}")
        prov = getattr(node, "provenance", None) or Provenance()
        prov.confidence = "deprecated"
        node.provenance = prov
        self.log.append(f"deprecated {id_}")
        return id_

    def move(self, ref: str, to: int) -> str:
        id_ = self._resolve(ref)
        kind = I.kind_of(id_)
        bucket = self._bucket(kind)
        if id_ not in bucket:
            raise PatchError(f"unknown reference: {ref!r}")
        keys = list(bucket)
        node = bucket.pop(id_)
        keys.remove(id_)
        keys.insert(max(0, min(to, len(keys))), id_)
        for k in keys:
            bucket[k] = bucket.pop(k)
        bucket[id_] = node
        self.log.append(f"moved {id_} -> [{to}]")
        return id_

    # ---------- transaction ----------
    def commit(self) -> Model:
        findings = validate(self.model)
        blocking = [f for f in findings if f.code not in _ADVISORY]
        if blocking and self.strict:
            self.model = self._original  # rollback
            raise PatchError("patch rejected: " + "; ".join(str(f) for f in blocking[:6]))
        self.log.append(f"commit ({len(blocking)} blocking findings, {len(findings)} total)")
        return self.model


_ADVISORY = {"EMPTY_COMPONENT", "ORPHAN_COMPONENT"}


_LIST_REF_FIELDS = {"requires", "consumes", "produces", "mutates", "emits",
                    "invokes", "children", "components", "permissions", "fields",
                    "steps", "branches", "states"}
_SCALAR_REF_FIELDS = {"actor", "goal", "entry", "presents", "target", "invokes",
                      "from_", "action", "to", "source", "initial"}


def apply(model: Model, ops: list[tuple], strict: bool = True) -> Model:
    """Run ops atomically. `ops` is a list of (op, ref, kwargs) tuples."""
    original = model.model_copy(deep=True)
    tx = Transaction(copy.deepcopy(model), strict=strict)
    try:
        for op in ops:
            name, ref = op[0], op[1]
            kwargs = op[2] if len(op) > 2 else {}
            if name == "rename":
                tx.rename(ref, kwargs.get("to_name", ref), kwargs.get("to_id"))
            elif name == "modify":
                tx.modify(ref, **kwargs)
            elif name == "add":
                tx.add(kwargs.pop("kind", I.kind_of(ref)), ref, **kwargs)
            elif name == "remove":
                tx.remove(ref)
            elif name == "deprecate":
                tx.deprecate(ref)
            elif name == "move":
                tx.move(ref, kwargs.get("to", 0))
            else:
                raise PatchError(f"unknown op {name!r}")
    except PatchError:
        raise
    return tx.commit()


def apply_text(model: Model, text: str, strict: bool = True) -> tuple[Model, list[str]]:
    """Minimal patch DSL:

        patch {
          rename capability.archiveProject to_name: archive to_id: capability.project.archive
          modify surface.Dashboard presents: entity.project
          remove component.old
        }
    """
    body = text.strip()
    if body.startswith("patch"):
        body = body[body.index("{") + 1:body.rindex("}")]
    ops: list[tuple] = []
    cur: tuple | None = None
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(rename|modify|add|remove|deprecate|move)\s+(\S+)(.*)$", line)
        if m:
            if cur:
                ops.append(cur)
            cur = (m.group(1), m.group(2), {})
            for k, v in _pairs(m.group(3)):
                cur[2][k] = _coerce(k, v)
        elif cur:
            for k, v in _pairs(line):
                cur[2][k] = _coerce(k, v)
    if cur:
        ops.append(cur)
    new = apply(model, ops, strict=strict)
    return new, ops


_LIST_FIELDS = {"requires", "consumes", "produces", "mutates", "emits", "invokes",
                "children", "components", "permissions", "fields", "steps", "branches", "states"}


def _pairs(text: str) -> list[tuple[str, str]]:
    """Parse `k: v k2: v2 k3: a,b,c` into pairs. Values keep commas so lists survive."""
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^\s][^\s]*(?:\s*,\s*[^\s,]+)*)", text):
        out.append((m.group(1), m.group(2).strip()))
    # keys written with no value mean "clear this list"
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?=\s|$)", text):
        if not any(k == m.group(1) for k, _ in out):
            out.append((m.group(1), ""))
    return out


def _coerce(k: str, v: str):
    if k in _LIST_FIELDS:
        return [x.strip() for x in v.split(",") if x.strip()]
    if v in ("true", "false"):
        return v == "true"
    return v
