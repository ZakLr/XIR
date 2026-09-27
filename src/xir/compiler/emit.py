"""Compilers: HTML / React / A2UI / tests / docs emitters."""
from __future__ import annotations
from xir.ast.nodes import Experience

def to_html(exp: Experience) -> str:
    parts = [f"<h1>{exp.name}</h1>", f"<p>{exp.goal}</p>"]
    for s in exp.surfaces:
        parts.append(f"<section id='{s.name}'><h2>{s.name}</h2>")
        for c in s.components:
            parts.append(f"<div>{c}</div>")
        parts.append("</section>")
    return "\n".join(parts)

def to_react(exp: Experience) -> str:
    lines = [f"// {exp.name} — generated from XIR", f"export function {exp.name}() {{"]
    for s in exp.surfaces:
        lines.append(f"  // surface {s.name}: {s.presents} {s.states}")
    lines.append("  return null; }")
    return "\n".join(lines)

def to_a2ui(exp: Experience) -> str:
    return "\n".join(f"A2UI surface {s.name} presents {s.presents}" for s in exp.surfaces) or "A2UI empty"

def to_tests(exp: Experience) -> str:
    return "\n".join(f"test {f.name} actor={f.actor} steps={f.steps}" for f in exp.flows) or "no flows"

def to_docs(exp: Experience) -> str:
    L = [f"# {exp.name}", "", (exp.goal or ""), ""]
    for e in exp.entities:
        L.append(f"## Entity {e.name}: " + ", ".join(f"{k}: {v}" for k, v in e.attrs.items()))
    for c in exp.capabilities:
        L.append(f"## Capability {c.name} (in={c.input} out={c.output} requires={c.requires})")
    for s in exp.surfaces:
        L.append(f"## Surface {s.name}: presents {s.presents}, states {s.states}")
    for f in exp.flows:
        L.append(f"## Flow {f.name}: {' -> '.join(f.steps)}")
    return "\n".join(L)

def to_a11y(exp: Experience) -> str:
    lines = []
    for s in exp.surfaces:
        for comp in s.components:
            lines.append(f"{s.name}.{comp}: role=auto focusable=true name={comp}")
        for st in s.states:
            lines.append(f"{s.name} state {st}: announced=true")
    return "\n".join(lines) or "no surfaces"

def to_playwright(exp: Experience) -> str:
    L = ["import { test, expect } from '@playwright/test';", ""]
    for f in exp.flows:
        L.append(f"test('{f.name}', async ({{ page }}) => {{")
        for st in f.steps:
            L.append(f"  // step: {st}")
        L.append("});")
    return "\n".join(L)
