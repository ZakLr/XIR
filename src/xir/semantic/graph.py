"""Semantic graph: stable IDs, NetworkX, L0-L6 slicing."""
from __future__ import annotations
import networkx as nx
from pydantic import BaseModel
from xir.ast.nodes import Experience

class Node(BaseModel):
    id: str
    kind: str
    name: str
    attrs: dict = {}

def sid(kind: str, *parts: str) -> str:
    return f"{kind}." + ".".join(p.lower() for p in parts)

def build_graph(exp: Experience) -> nx.DiGraph:
    g = nx.DiGraph()
    root = "exp." + exp.name.lower()
    g.add_node(root, kind="experience", name=exp.name)
    for e in exp.entities:
        i = sid("entity", e.name)
        g.add_node(i, kind="entity", name=e.name)
        g.add_edge(root, i, rel="has")
        for a in e.attrs:
            aid = sid("entity", e.name, a)
            g.add_node(aid, kind="attribute", name=a)
            g.add_edge(i, aid, rel="has")
    for c in exp.capabilities:
        i = sid("capability", c.name)
        g.add_node(i, kind="capability", name=c.name)
        g.add_edge(root, i, rel="has")
        for r in c.requires:
            g.add_edge(i, f"perm.{r}", rel="requires")
        if c.output:
            g.add_edge(i, sid("entity", c.output), rel="produces")
    for s in exp.surfaces:
        i = sid("surface", s.name)
        g.add_node(i, kind="surface", name=s.name)
        g.add_edge(root, i, rel="has")
        for comp in s.components:
            cid = sid("component", s.name, comp)
            g.add_node(cid, kind="component", name=comp)
            g.add_edge(i, cid, rel="contains")
        for st in s.states:
            stid = sid("state", s.name, st)
            g.add_node(stid, kind="state", name=st)
            g.add_edge(i, stid, rel="has-state")
    for f in exp.flows:
        i = sid("flow", f.name)
        g.add_node(i, kind="flow", name=f.name)
        g.add_edge(root, i, rel="has")
        prev = None
        for st in f.steps:
            nid = sid("flow", f.name, st)
            g.add_node(nid, kind="flow-step", name=st)
            g.add_edge(i, nid, rel="has-step")
            if prev:
                g.add_edge(prev, nid, rel="next")
            prev = nid
    return g

LEVELS = {0: "Product summary", 1: "Experience/domain", 2: "Capability/flow",
          3: "Surface", 4: "Component", 5: "State", 6: "Implementation"}

def summarize(exp: Experience, level: int = 0) -> str:
    if level == 0:
        v = f" v{exp.version}" if exp.version else ""
        return f"{exp.name}{v}: {exp.goal} [{len(exp.entities)} entities, {len(exp.capabilities)} caps, {len(exp.surfaces)} surfaces, {len(exp.flows)} flows]"
    lines = [summarize(exp, 0)]
    if level >= 1:
        lines += [f"entity.{e.name}: {e.attrs}" + (f" prov={e.provenance}" if e.provenance else "") for e in exp.entities]
    if level >= 2:
        lines += [f"capability.{c.name}: in={c.input} out={c.output} requires={c.requires} effects={c.effects}" for c in exp.capabilities]
        lines += [f"flow.{f.name}: actor={f.actor} steps={f.steps}" for f in exp.flows]
    if level >= 3:
        lines += [f"surface.{s.name}: presents={s.presents} states={s.states} components={s.components}" for s in exp.surfaces]
    if level >= 4:
        for s in exp.surfaces:
            for comp in s.components:
                lines.append(f"component.{s.name}.{comp}: surface={s.name}")
    if level >= 5:
        for s in exp.surfaces:
            for st in s.states:
                lines.append(f"state.{s.name}.{st}: surface={s.name}")
    if level >= 6:
        lines += ["mapping: semantic->HTML/React/A2UI via compiler/emit.py; capability->tool via requires/permissions"]
        lines += [f"meta.{m.kind}: \"{m.text}\"" for m in exp.meta]
    return "\n".join(lines)
