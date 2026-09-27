"""Canonical XIR serializer: semantic IR -> source text.

Round-trip is semantic, not textual (§34): parse(serialize(ir)) must yield the same
model. The serializer emits the modern, explicit form; the parser still accepts the
legacy flat form, so old files keep working (§31).
"""
from __future__ import annotations
from xir.ir.model import Model, Rel


def _prov(prov, indent: str) -> list[str]:
    out: list[str] = []
    if prov is None:
        return out
    if prov.source and prov.confidence and prov.confidence != "unknown":
        out = [f"{indent}provenance {{ source: {prov.source} confidence: {prov.confidence}"]
        if prov.reference:
            out[-1] += f" reference: {prov.reference}"
        out[-1] += " }"
    return out


def to_xir(m: Model) -> str:
    L: list[str] = [f"experience {m.name} {{"]
    if m.goal:
        L.append(f'  goal: "{m.goal}"')
    if m.version:
        L.append(f"  version: {m.version}")
    L.append("")

    for n in m.meta.values():
        L.append(f'  {n.kind} {n.name} {{')
        if n.claim:
            L.append(f'    claim: "{n.claim}"')
        if n.confidence and n.confidence != "unknown":
            L.append(f"    confidence: {n.confidence}")
        if n.evidence:
            L.append("    evidence { " + " ".join(n.evidence) + " }")
        L.append("  }")

    for g in m.goals.values():
        L.append(f"  goal {g.name} {{")
        if g.description:
            L.append(f'    description: "{g.description}"')
        if g.actor:
            L.append(f"    actor: {g.actor}")
        L.append("  }")

    for p in m.permissions.values():
        L.append(f"  permission {p.name} {{")
        if p.description:
            L.append(f'    description: "{p.description}"')
        L.append("  }")

    for a in m.actors.values():
        L.append(f"  actor {a.name} {{")
        if a.permissions:
            L.append("    permissions { " + " ".join(a.permissions) + " }")
        L.append("  }")

    for e in m.entities.values():
        L.append(f"  entity {e.name} {{")
        for f in e.fields:
            fld = m.fields.get(f)
            if fld:
                L.append(f"    {fld.name}: {fld.type}")
        L += _prov(e.provenance, "    ")
        L.append("  }")

    for ev in m.events.values():
        L.append(f"  event {ev.name}")

    for c in m.capabilities.values():
        L.append(f"  capability {c.name} {{")
        L.append(f"    id: {c.id}")
        if c.input:
            L.append("    input { " + "  ".join(f"{k}: {v}" for k, v in c.input.items()) + " }")
        if c.output:
            L.append(f"    output: {c.output}")
        if c.requires:
            L.append("    requires: " + " ".join(c.requires))
        if c.consumes:
            L.append("    consumes: " + " ".join(c.consumes))
        # `output` already implies production; do not emit it twice
        extra_produces = [p for p in c.produces if p != c.output]
        if extra_produces:
            L.append("    produces: " + " ".join(extra_produces))
        if c.mutates:
            L.append("    mutates { " + " ".join(c.mutates) + " }")
        if c.emits:
            L.append("    emits: " + " ".join(c.emits))
        if c.confirmation:
            L.append("    confirmation: required")
        if c.audit:
            L.append("    audit: required")
        L += _prov(c.provenance, "    ")
        L.append("  }")

    for i in m.interactions.values():
        L.append(f"  interaction {i.name} {{")
        L.append(f"    id: {i.id}")
        L.append(f"    trigger: {i.trigger}")
        if i.target:
            L.append(f"    target: {i.target}")
        if i.invokes:
            L.append(f"    invokes: {i.invokes}")
        L.append("  }")

    for c in m.components.values():
        if getattr(c, "legacy", False):
            continue
        L.append(f"  component {c.name} {{")
        L.append(f"    id: {c.id}")
        if c.presents:
            L.append(f"    presents: {c.presents}")
        if c.invokes:
            L.append("    invokes: " + " ".join(c.invokes))
        if c.states:
            L.append("    states { " + " ".join(c.states) + " }")
        if c.children:
            L.append("    contains { " + " ".join(c.children) + " }")
        L.append("  }")

    for mc in m.machines.values():
        if not mc.states or not mc.transitions:
            continue  # legacy bare state lists are regenerated from the surface
        L.append(f"  state {mc.name} {{")
        if mc.initial:
            init = m.states.get(mc.initial)
            L.append(f"    initial: {init.name if init else mc.initial}")
        for st in mc.states:
            node = m.states.get(st)
            if node is None:
                continue
            L.append(f"    {node.name} {{")
            for tid in mc.transitions:
                t = m.transitions.get(tid)
                if t is None or t.source != st or not t.event:
                    continue
                tgt = m.states.get(t.target)
                line = f"      on {t.event}"
                if t.guard:
                    line += f" when {t.guard}"
                if t.action:
                    line += f" do {t.action}"
                line += f" -> {tgt.name if tgt else t.target}"
                L.append(line)
            L.append("    }")
        L.append("  }")

    for s in m.surfaces.values():
        L.append(f"  surface {s.name} {{")
        L.append(f"    id: {s.id}")
        if s.presents:
            L.append(f"    presents: {s.presents}")
        if s.components:
            names = [m.components[c].name if c in m.components else c for c in s.components]
            L.append("    components { " + " ".join(names) + " }")
        # a machine with transitions is emitted as its own `state` block and referenced;
        # a bare state list is emitted inline so the legacy form round-trips
        for mk in s.states:
            mc = m.machines.get(mk)
            if mc is None:
                continue
            if mc.transitions:
                L.append(f"    machine: {mk}")
            elif mc.states:
                L.append("    states: " + " ".join(
                    m.states[x].name for x in mc.states if x in m.states))
        L += _prov(s.provenance, "    ")
        L.append("  }")

    for f in m.flows.values():
        L.append(f"  flow {f.name} {{")
        L.append(f"    id: {f.id}")
        if f.goal:
            L.append(f"    goal: {f.goal}")
        if f.actor:
            L.append(f"    actor: {f.actor}")
        if f.entry:
            L.append("    entry { surface: " + f.entry + " }")
        for sid in f.steps:
            st = m.steps.get(sid)
            if st is None:
                continue
            L.append(f"    step {st.name} {{")
            if st.from_:
                L.append(f"      from: {st.from_}")
            if st.action:
                L.append(f"      action: {st.action}")
            if st.to:
                L.append(f"      to: {st.to}")
            L.append("    }")
        for bid in f.branches:
            b = m.branches.get(bid)
            if b is None:
                continue
            L.append(f"    branch {b.name} {{")
            if b.from_:
                L.append(f"      from: {b.from_}")
            for guard, target in b.cases:
                L.append(f"      {guard} -> {target}")
            L.append("    }")
        L.append("  }")

    for inv in m.invariants.values():
        L.append(f"  invariant {inv.id.split('.')[-1]} {{")
        L.append(f'    rule: "{inv.rule}"')
        if inv.scope:
            L.append(f"    scope: {inv.scope}")
        L.append("  }")

    L.append("}")
    return "\n".join(L) + "\n"
