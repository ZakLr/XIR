"""Query engine — slicing by id/kind + include selection."""
from __future__ import annotations
import re
from xir.ast.nodes import Experience

def query(exp: Experience, q: str) -> str:
    ql = q.lower()
    inc = set(re.findall(r"include\s*:?\s*([\w\s,]+)", ql))
    includes = set(re.split(r"[\s,]+", " ".join(inc))) if inc else set()
    if "capability" in ql:
        lines = []
        for c in exp.capabilities:
            parts = [f"{c.name}: in={c.input} out={c.output}"]
            if not includes or "permissions" in includes or "requires" in includes:
                parts.append(f"requires={c.requires}")
            if not includes or "effects" in includes:
                parts.append(f"effects={c.effects}")
            if not includes or "callers" in includes:
                callers = [s.name for s in exp.surfaces if c.name in s.components] + \
                          [f.name for f in exp.flows if c.name in f.steps]
                parts.append(f"callers={callers}")
            if c.provenance and (not includes or "provenance" in includes):
                parts.append(f"prov={c.provenance}")
            lines.append(" ".join(parts))
        return "\n".join(lines) or "no capabilities"
    if "surface" in ql:
        lines = []
        for s in exp.surfaces:
            parts = [f"{s.name}:"]
            if not includes or "layout" in includes:
                parts.append(f"presents={s.presents} components={s.components}")
            if not includes or "interactions" in includes:
                caps = [c.name for c in exp.capabilities if c.name in s.components]
                parts.append(f"interactions={caps}")
            if not includes or "states" in includes:
                parts.append(f"states={s.states}")
            lines.append(" ".join(parts))
        return "\n".join(lines) or "no surfaces"
    if "component" in ql:
        return "\n".join(f"{s.name}.{c}: semantic=component states={s.states}" for s in exp.surfaces for c in s.components) or "no components"
    if "state" in ql:
        return "\n".join(f"{s.name}.{st}" for s in exp.surfaces for st in s.states) or "no states"
    if "flow" in ql:
        return "\n".join(f"{f.name}: actor={f.actor} steps={f.steps}" for f in exp.flows) or "no flows"
    if "entity" in ql or "domain" in ql:
        return "\n".join(f"{e.name}: {e.attrs}" for e in exp.entities) or "no entities"
    if "mutat" in ql:
        return "\n".join(f"{c.name} -> {c.effects}" for c in exp.capabilities if c.effects) or "none"
    if "guest" in ql or re.search(r"\bcan\b|\bdo\b|what can", ql):
        return "\n".join(f"{c.name} requires {c.requires or 'nothing'}" for c in exp.capabilities)
    if "paths to" in ql or "show all paths" in ql:
        m = re.search(r"paths to (\w+)", ql)
        target = m.group(1) if m else ""
        return "\n".join(f"{f.name}: {' -> '.join(f.steps)}" for f in exp.flows if not target or target in f.steps or target == f.name) or "no paths"
    if "changed between" in ql or "what changed" in ql:
        return "use: xir diff old.xir new.xir"
    if "what happens when" in ql or "fails" in ql:
        return "\n".join(f"{f.name}: actor={f.actor} steps={f.steps}" for f in exp.flows) or "no flows"
    return f"{exp.name}: {exp.goal}"

def inspect(exp: Experience, kind: str, name: str) -> str:
    kl = kind.lower()
    if kl == "surface":
        s = next((x for x in exp.surfaces if x.name.lower() == name.lower()), None)
        return f"{s.name}: presents={s.presents} states={s.states} components={s.components}" if s else f"unknown surface {name}"
    if kl == "capability":
        return trace_capability(exp, name)
    if kl == "flow":
        f = next((x for x in exp.flows if x.name.lower() == name.lower()), None)
        return f"{f.name}: actor={f.actor} steps={f.steps}" if f else f"unknown flow {name}"
    if kl == "component":
        for s in exp.surfaces:
            if name in s.components:
                return f"{s.name}.{name}: semantic=component states={s.states}"
        return f"unknown component {name}"
    return query(exp, f"{kind} {name}")

def explain(exp: Experience, kind: str, name: str) -> str:
    if kind.lower() == "capability":
        return trace_capability(exp, name)
    if kind.lower() == "decision":
        return "\n".join(f"{m.kind}: \"{m.text}\"" for m in exp.meta if m.kind == "decision") or "no decisions recorded"
    return inspect(exp, kind, name)

def trace_capability(exp: Experience, name: str) -> str:
    out = [f"trace capability.{name}"]
    for s in exp.surfaces:
        if name in s.components or name == s.presents:
            out.append(f"exposed by surface.{s.name}")
    for f in exp.flows:
        if name in f.steps or any(name.lower() in st.lower() for st in f.steps):
            out.append(f"affects flow.{f.name}")
    c = next((x for x in exp.capabilities if x.name == name), None)
    if c:
        out.append(f"requires={c.requires} effects={c.effects}")
    return "\n".join(out)
