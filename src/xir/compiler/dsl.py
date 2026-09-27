"""Canonical DSL emitter + light HTML extractor (round-trip v0.1)."""
from __future__ import annotations
import re
from xir.ast.nodes import Experience

def _prov(prov: dict, indent: str = "    ") -> list[str]:
    if not prov:
        return []
    return [f"{indent}provenance {{ " + " ".join(f"{k}: {v}" for k, v in prov.items()) + " }"]

def to_xir(exp: Experience) -> str:
    L = [f"experience {exp.name} {{"]
    if exp.goal:
        L.append(f'  goal: "{exp.goal}"')
    if exp.version:
        L.append(f"  version: {exp.version}")
    if exp.actors:
        L.append("  actors { " + " ".join(exp.actors) + " }")
    for m in exp.meta:
        L.append(f'  {m.kind}: "{m.text}"')
    for e in exp.entities:
        attrs = "  ".join(f"{k}: {v}" for k, v in e.attrs.items())
        if e.provenance:
            L.append(f"  entity {e.name} {{ {attrs}")
            L += _prov(e.provenance)
            L.append("  }")
        else:
            L.append(f"  entity {e.name} {{ {attrs} }}")
    for c in exp.capabilities:
        L.append(f"  capability {c.name} {{")
        if c.input:
            L.append("    input { " + "  ".join(f"{k}: {v}" for k, v in c.input.items()) + " }")
        if c.output:
            L.append(f"    output: {c.output}")
        if c.requires:
            L.append("    requires: " + " ".join(c.requires))
        for fx in c.effects:
            L.append(f"    effects: {fx}")
        if c.confirmation:
            L.append("    confirmation: required")
        if c.audit:
            L.append("    audit: required")
        L += _prov(c.provenance)
        L.append("  }")
    for s in exp.surfaces:
        L.append(f"  surface {s.name} {{")
        if s.presents:
            L.append(f"    presents: {s.presents}")
        if s.components:
            L.append("    components { " + " ".join(s.components) + " }")
        if s.states:
            L.append("    states: " + " ".join(s.states))
        L += _prov(s.provenance)
        L.append("  }")
    for f in exp.flows:
        L.append(f"  flow {f.name} {{")
        if f.actor:
            L.append(f"    actor: {f.actor}")
        for i in range(0, len(f.steps) - 1, 2):
            L.append(f"    {f.steps[i]} -> {f.steps[i+1]}")
        L += _prov(f.provenance)
        L.append("  }")
    L.append("}")
    return "\n".join(L) + "\n"

def extract_html(html: str) -> Experience:
    """Light extractor: h1 -> experience, sections -> surfaces. Proves impl->DSL direction."""
    from xir.ast.nodes import Experience, Surface
    m = re.search(r"<h1>(.*?)</h1>", html)
    name = m.group(1) if m else "Extracted"
    surfaces = [Surface(n) for n in re.findall(r"<section id='(.*?)'>", html)]
    return Experience(name=name, surfaces=surfaces)
