"""Multi-resolution context projection (L0..L6).

An agent should never need the whole model. Each level is a strict refinement of
the one above it, and every line carries the semantic id it came from.
"""
from __future__ import annotations
from xir.ir.model import Model

LEVELS = {
    0: "product summary",
    1: "experience / domain",
    2: "capability / flow",
    3: "surface",
    4: "component",
    5: "state",
    6: "implementation",
}


def summarize(m: Model, level: int = 0) -> str:
    L: list[str] = []
    v = f" v{m.version}" if m.version else ""
    L.append(f"{m.name}{v} [{m.id}]: {m.goal}")
    L.append(f"  {len(m.entities)} entities, {len(m.capabilities)} capabilities, "
             f"{len(m.surfaces)} surfaces, {len(m.flows)} flows, "
             f"{len(m.states)} states, {len(m.transitions)} transitions")
    if level >= 1:
        for e in m.entities.values():
            fields = ", ".join(f"{m.fields[f].name}: {m.fields[f].type}"
                               for f in e.fields if f in m.fields)
            L.append(f"ENTITY {e.id} {fields}")
        for a in m.actors.values():
            L.append(f"ACTOR {a.id} -> {a.permissions}")
        for p in m.permissions.values():
            L.append(f"PERMISSION {p.id} {p.description}")
        for g in m.goals.values():
            L.append(f"GOAL {g.id} {g.description} actor={g.actor}")
    if level >= 2:
        for c in m.capabilities.values():
            L.append(f"CAPABILITY {c.id} in={c.input} out={c.output} "
                     f"requires={c.requires} mutates={c.mutates} emits={c.emits}")
        for f in m.flows.values():
            L.append(f"FLOW {f.id} actor={f.actor} goal={f.goal} entry={f.entry} "
                     f"steps={len(f.steps)} branches={len(f.branches)}")
    if level >= 3:
        for s in m.surfaces.values():
            L.append(f"SURFACE {s.id} presents={s.presents} components={s.components} "
                     f"machine={s.states}")
    if level >= 4:
        for c in m.components.values():
            L.append(f"COMPONENT {c.id} presents={c.presents} invokes={c.invokes} "
                     f"states={c.states}")
        for i in m.interactions.values():
            L.append(f"INTERACTION {i.id} {i.trigger} on {i.target} -> {i.invokes}")
    if level >= 5:
        for mc in m.machines.values():
            L.append(f"MACHINE {mc.id} initial={mc.initial} transitions={len(mc.transitions)}")
            for st in mc.states:
                n = m.states.get(st)
                L.append(f"  STATE {st} {n.name if n else ''}")
            for tid in mc.transitions:
                t = m.transitions.get(tid)
                if t and t.event:
                    L.append(f"    on {t.event} -> {t.target}"
                             + (f" when {t.guard}" if t.guard else ""))
    if level >= 6:
        L.append("METADATA " + "; ".join(f"{n.kind}={n.claim} ({n.confidence})"
                                          for n in m.meta.values()))
        L.append("INVARIANTS " + "; ".join(i.rule for i in m.invariants.values()))
        L.append("PROJECTIONS react html a2ui docs a11y playwright xir")
    return "\n".join(L)
