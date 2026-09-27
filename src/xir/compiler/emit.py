"""Compiler targets.

`to_react` is the one serious runtime target (§23): it emits components, state,
interactions, capability calls, transitions and loading/empty/error states derived
from the semantic graph. The other emitters are useful projections but stay shallow.
"""
from __future__ import annotations
from xir.ir.model import Model, Rel
from xir.semantic.graph import Graph

# ---------------------------------------------------------------- semantic React


def to_react(m: Model) -> str:
    g = Graph(m)
    L: list[str] = []
    L.append("// Generated from XIR semantic model. Do not edit by hand.")
    L.append("// Each surface, component, capability and state below is traceable to a semantic id.")
    L.append("import React, { useState, useCallback } from 'react';")
    L.append("")
    for ev in m.events.values():
        L.append(f"// event {ev.id} ({ev.name})")
    L.append("")
    L.append("export const capabilities = {")
    for cid, c in m.capabilities.items():
        L.append(f"  {c.name}: {{ id: '{cid}', requires: {c.requires!r}, mutates: {c.mutates!r},"
                 f" emits: {c.emits!r}, confirmation: {str(c.confirmation).lower()}, audit: {str(c.audit).lower()} }},")
    L.append("};")
    L.append("")
    for mk, mc in m.machines.items():
        L += _react_machine(m, g, mc)
    for ck, c in m.components.items():
        L += _react_component(m, g, c)
    for sk, s in m.surfaces.items():
        L += _react_surface(m, g, s)
    L.append(f"export default function {m.name}() {{ return <div data-xir=\"{m.id}\" />; }}")
    return "\n".join(L)


def _react_machine(m: Model, g: Graph, mc) -> list[str]:
    if not mc.states:
        return []
    L = [f"// state machine {mc.id}"]
    L.append(f"const initial{mc.name} = {mc.initial!r};")
    for st in mc.states:
        s = m.states.get(st)
        if s is None:
            continue
        L.append(f"const {s.name} = {{ id: {st!r}, name: {s.name!r} }};")
    L.append(f"const transitions{mc.name} = {{")
    for tid in mc.transitions:
        t = m.transitions.get(tid)
        if t is None or not t.event:
            continue
        guard = f" // {t.guard}" if t.guard else ""
        L.append(f"  {t.event!r}: {{ from: {t.source!r}, to: {t.target!r} }}{guard},")
    L.append("};")
    L.append(f"function use{mc.name}(initial = {mc.initial!r}) {{")
    L.append("  const [state, setState] = useState(initial);")
    L.append("  const send = useCallback((event) => {")
    L.append("    const t = transitions" + mc.name + "[event];")
    L.append("    if (t && t.from === state) setState(t.to);")
    L.append("  }, [state]);")
    L.append("  return [state, send];")
    L.append("}")
    return L + [""]


def _react_component(m: Model, g: Graph, c) -> list[str]:
    L = [f"// component {c.id}"]
    if c.presents:
        L.append(f"// presents {c.presents}")
    for inv in c.invokes:
        cap = m.capabilities.get(inv)
        if cap is None:
            continue
        L.append(f"async function on{cap.name}() {{")
        L.append(f"  // capability {cap.id}")
        L.append(f"  if ({cap.confirmation!r}) {{ /* confirm required */ }}")
        for e in cap.emits:
            L.append(f"  dispatch({e!r});")
        for f in cap.mutates:
            L.append(f"  set({f!r});")
        L.append("}")
    for iid in g.out(c.id, Rel.HAS_INTERACTION):
        it = m.interactions.get(iid)
        if it is None:
            continue
        L.append(f"// interaction {it.id}: {it.trigger} -> {it.invokes}")
        L.append(f"const {it.name}Interaction = {{ trigger: {it.trigger!r}, invokes: {it.invokes!r} }};")
    for mk in c.states:
        mc = m.machines.get(mk)
        if mc is not None:
            L.append(f"// uses machine {mc.id}")
    L.append(f"export function {c.name}({{ onEvent = () => {{}} }} = {{}}) {{")
    L.append("  return <div data-xir=\"" + c.id + "\" data-name=\"" + c.name + "\" />;")
    L.append("}")
    return L + [""]


def _react_surface(m: Model, g: Graph, s) -> list[str]:
    L = [f"// surface {s.id}"]
    if s.presents:
        L.append(f"// presents {s.presents}")
    machine = next((m.machines[x] for x in s.states if x in m.machines), None)
    if machine is not None:
        L.append(f"export function {s.name}View() {{")
        L.append(f"  const [state, send] = use{machine.name}();")
        for st in machine.states:
            node = m.states.get(st)
            if node is not None:
                L.append(f"  if (state === {st!r}) return <{s.name}State name={{{node.name!r}}} />;")
        L.append("  return null;")
        L.append("}")
    L.append(f"export function {s.name}State({{ name }}) {{ return <section data-state={{name}} />; }}")
    return L + [""]


# ---------------------------------------------------------------- semantic Playwright (§24)


def to_playwright(m: Model) -> str:
    g = Graph(m)
    L = ["// Playwright tests generated from the semantic graph.",
         "// Each test walks interaction -> capability -> permission -> mutation -> event -> state.",
         "import { test, expect } from '@playwright/test';", ""]
    for iid, it in m.interactions.items():
        cap = m.capabilities.get(it.invokes or "")
        if cap is None:
            continue
        comp = m.components.get(it.target or "")
        surf = g.inc(it.target, Rel.CONTAINS)[0] if it.target and g.inc(it.target, Rel.CONTAINS) else None
        L.append(f"test('{it.name}', async ({{ page }}) => {{")
        if surf:
            L.append(f"  await page.goto('/{m.surfaces[surf].name.lower()}');")
        if comp:
            L.append(f"  // component {comp.id}")
            L.append(f"  await page.getByTestId('{comp.id}').click();")
        L.append(f"  // interaction {it.id} ({it.trigger}) invokes {cap.id}")
        if cap.confirmation:
            L.append("  await expect(page.getByRole('dialog')).toBeVisible();")
            L.append("  await page.getByRole('button', { name: /confirm/i }).click();")
        for p in cap.requires:
            L.append(f"  // requires {p}")
        for mu in cap.mutates:
            L.append(f"  await expect(page.getByTestId('{mu}')).toHaveText(/archived/i);")
        for e in cap.emits:
            L.append(f"  // expect event {e}")
        for tid in g.out(cap.id, Rel.CAUSES):
            t = m.transitions.get(tid)
            if t and t.target:
                L.append(f"  await expect(page.getByTestId('{t.target}')).toBeVisible();")
        L.append("});")
        L.append("")
    for fid, f in m.flows.items():
        L.append(f"test('flow {f.name}', async ({{ page }}) => {{")
        for sid in f.steps:
            st = m.steps.get(sid)
            if st is None:
                continue
            L.append(f"  // step {st.id}: {st.from_} --{st.action}--> {st.to}")
        L.append("});")
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- other projections


def to_html(m: Model) -> str:
    g = Graph(m)
    parts = [f"<h1>{m.name}</h1>", f"<p>{m.goal}</p>"]
    for s in m.surfaces.values():
        parts.append(f"<section id='{s.name}' data-xir='{s.id}'><h2>{s.name}</h2>")
        for c in s.components:
            parts.append(f"<div data-xir='{c}'>{g.name(c)}</div>")
        parts.append("</section>")
    return "\n".join(parts)


def to_a2ui(m: Model) -> str:
    return "\n".join(f"A2UI surface {s.name} presents {s.presents} [{s.id}]"
                     for s in m.surfaces.values()) or "A2UI empty"


def to_tests(m: Model) -> str:
    return "\n".join(f"test {f.name} actor={f.actor} steps={len(f.steps)} branches={len(f.branches)}"
                     for f in m.flows.values()) or "no flows"


def to_docs(m: Model) -> str:
    L = [f"# {m.name}", "", (m.goal or ""), ""]
    for e in m.entities.values():
        L.append(f"## Entity {e.name}: " + ", ".join(
            f"{m.fields[f].name}: {m.fields[f].type}" for f in e.fields if f in m.fields))
    for c in m.capabilities.values():
        L.append(f"## Capability {c.name} `{c.id}`")
        L.append(f"- requires: {c.requires}")
        L.append(f"- mutates: {c.mutates}")
        L.append(f"- emits: {c.emits}")
    for s in m.surfaces.values():
        L.append(f"## Surface {s.name} `{s.id}` — components {s.components}")
    for f in m.flows.values():
        L.append(f"## Flow {f.name} `{f.id}` — actor {f.actor}, goal {f.goal}")
    return "\n".join(L)


def to_a11y(m: Model) -> str:
    lines = []
    for s in m.surfaces.values():
        for c in s.components:
            lines.append(f"{c}: role=region name={m.components[c].name if c in m.components else c} focusable=true")
        for mk in s.states:
            mc = m.machines.get(mk)
            if mc:
                for st in mc.states:
                    lines.append(f"{st}: aria-live=polite announced=true")
    return "\n".join(lines) or "no surfaces"


# One registry for every emitter, so the CLI, the MCP server and the docs
# cannot disagree about which targets exist.
def _registry() -> "dict[str, Callable[[Model], str]]":
    from xir.compiler.dsl import to_xir
    return {"react": to_react, "html": to_html, "a2ui": to_a2ui, "docs": to_docs,
            "a11y": to_a11y, "playwright": to_playwright, "tests": to_tests,
            "xir": to_xir}


TARGETS: "dict[str, Callable[[Model], str]]" = _registry()


def emit(m: "Model", target: str) -> str:
    """Render the model with the named emitter."""
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; "
                         f"expected one of {', '.join(sorted(TARGETS))}")
    return TARGETS[target](m)
