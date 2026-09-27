"""Validator — first-class checks (PROMPT Sec 47)."""
from __future__ import annotations
from xir.ast.nodes import Experience

_PRIMITIVES = {"Text", "ID", "Int", "Bool", "Float"}
_REQUIRED_STATES = {"loading", "error"}
_SOURCES = {"human", "requirement-document", "code", "design", "API", "test", "analytics", "inference", "agent"}
_CONF = {"confirmed", "probable", "inferred", "tentative", "proposed", "deprecated", "unknown"}

def validate(exp: Experience) -> list[str]:
    errs: list[str] = []
    seen: set[str] = set()
    for kind, items in (("entity", exp.entities), ("capability", exp.capabilities),
                        ("surface", exp.surfaces), ("flow", exp.flows)):
        for it in items:
            key = f"{kind}.{it.name}"
            if key in seen:
                errs.append(f"duplicate ID: {key}")
            seen.add(key)
    ent = {e.name for e in exp.entities}
    caps = {c.name for c in exp.capabilities}
    surfs = {s.name for s in exp.surfaces}
    flows = {f.name for f in exp.flows}
    actors = set(exp.actors)
    # undefined refs: input/output types
    for c in exp.capabilities:
        if not c.input and not c.output:
            errs.append(f"invalid capability: capability.{c.name} has no input/output")
        for _, t in c.input.items():
            for alt in t.split("|"):
                base = alt.strip().split("[")[0].strip().rstrip("s")
                if base and base not in ent and base not in _PRIMITIVES:
                    errs.append(f"undefined reference: capability.{c.name} input type '{base}'")
        if c.output and c.output not in ent:
            errs.append(f"undefined reference: capability.{c.name} output '{c.output}'")
    # surfaces
    for s in exp.surfaces:
        if not s.states:
            errs.append(f"missing states: surface.{s.name} should declare loading/empty/populated/error")
        else:
            missing = _REQUIRED_STATES - {x.lower() for x in s.states}
            if missing:
                errs.append(f"missing required states: surface.{s.name} lacks {sorted(missing)}")
            if len(s.states) == 1:
                errs.append(f"missing transitions: surface.{s.name} has single state, no transitions possible")
        if s.presents:
            base = s.presents.split("[")[0].split(".")[0]
            if base and base not in ent and base != s.presents:
                errs.append(f"inconsistent domain: surface.{s.name} presents unknown entity '{base}'")
    # flows
    for f in exp.flows:
        if not f.steps:
            errs.append(f"dead-end flow: flow.{f.name} has no steps")
            continue
        if f.actor and actors and f.actor not in actors:
            errs.append(f"broken reference: flow.{f.name} actor '{f.actor}' not in actors {sorted(actors)}")
        unknowns = [st for st in f.steps if st not in surfs and st not in caps and st not in ent and st not in flows and st.lower() not in
                    ("validating", "loading", "error", "retry", "success", "validation", "permission", "network")]
        # only flag if step looks like a ref but unknown AND flow has known surfaces (avoid noise)
        for st in unknowns:
            if st in (f.name,) or st.lower() in f.name.lower() or f.name.lower() in st.lower():
                continue
            errs.append(f"unreachable state: flow.{f.name} step '{st}' matches no surface/capability")
            break
        if len(set(f.steps)) == 1 and len(f.steps) > 1:
            errs.append(f"circular dependency: flow.{f.name} loops on single step '{f.steps[0]}'")
    # destructive without confirmation
    for c in exp.capabilities:
        if any(k in c.name.lower() for k in ("delete", "destroy", "archive", "remove")) and not c.confirmation:
            errs.append(f"invalid permissions: capability.{c.name} is destructive but lacks confirmation")
    # provenance: valid source/confidence; inference must not claim confirmed
    for kind, items in (("entity", exp.entities), ("capability", exp.capabilities),
                        ("surface", exp.surfaces), ("flow", exp.flows)):
        for it in items:
            p = it.provenance or {}
            if p.get("source") and p["source"] not in _SOURCES:
                errs.append(f"invalid provenance: {kind}.{it.name} unknown source '{p['source']}'")
            if p.get("confidence") and p["confidence"] not in _CONF:
                errs.append(f"invalid provenance: {kind}.{it.name} unknown confidence '{p['confidence']}'")
            if p.get("source") == "inference" and p.get("confidence") == "confirmed":
                errs.append(f"invalid provenance: {kind}.{it.name} inference cannot claim confirmed")
    for m in exp.meta:
        if m.kind == "inference":
            errs.append(f"inference flagged: {m.kind}: \"{m.text}\" must not become requirement without evidence")
    return errs
