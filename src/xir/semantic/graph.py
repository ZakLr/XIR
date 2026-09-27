"""Typed semantic graph (§13, §14).

Built from the semantic IR only. Every edge carries a relation from `Rel`.
Edges are added only where the IR asserts a relationship — never because two
names merely co-occur in a declaration.
"""
from __future__ import annotations
import networkx as nx
from pydantic import BaseModel, Field
from xir.ir.model import Model, Rel
from xir.ir.ids import kind_of

class Node(BaseModel):
    id: str
    kind: str
    name: str
    attrs: dict = Field(default_factory=dict)

class Edge(BaseModel):
    source: str
    relation: str
    target: str

_BUCKET_KINDS = ("goal", "actor", "permission", "entity", "field", "event", "capability",
                 "surface", "component", "interaction", "machine", "state", "transition",
                 "flow", "step", "branch", "invariant", "meta")


class Graph:
    """Thin typed wrapper. `g` is a NetworkX DiGraph of Node/Edge payloads."""

    def __init__(self, model: Model):
        self.model = model
        self.g = nx.DiGraph()
        self._build()

    # ---------- construction ----------
    def _node(self, id_: str, node_kind: str, name: str, **attrs):
        self.g.add_node(id_, payload=Node(id=id_, kind=node_kind, name=name, attrs=attrs))

    def _edge(self, a: str, rel: str, b: str, **attrs):
        if a not in self.g or b not in self.g:
            return
        self.g.add_edge(a, b, payload=Edge(source=a, relation=rel, target=b), rel=rel, **attrs)

    def _build(self):
        m = self.model
        self._node(m.id, "experience", m.name, version=m.version, goal=m.goal)

        for k, node in m.goals.items():
            self._node(k, "goal", node.name, description=node.description)
            self._edge(m.id, Rel.HAS, k)
            if node.actor:
                self._edge(k, Rel.ACHIEVED_BY, node.actor)
        for k, node in m.actors.items():
            self._node(k, "actor", node.name)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.permissions.items():
            self._node(k, "permission", node.name, description=node.description)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.entities.items():
            self._node(k, "entity", node.name)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.fields.items():
            self._node(k, "field", node.name, type=node.type)
        for k, node in m.events.items():
            self._node(k, "event", node.name)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.capabilities.items():
            self._node(k, "capability", node.name, confirmation=node.confirmation, audit=node.audit)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.surfaces.items():
            self._node(k, "surface", node.name)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.components.items():
            self._node(k, "component", node.name)
        for k, node in m.interactions.items():
            self._node(k, "interaction", node.name, trigger=node.trigger)
        for k, node in m.machines.items():
            self._node(k, "machine", node.name, initial=node.initial)
        for k, node in m.states.items():
            self._node(k, "state", node.name)
        for k, node in m.transitions.items():
            self._node(k, "transition", node.name, event=node.event, guard=node.guard)
        for k, node in m.flows.items():
            self._node(k, "flow", node.name)
            self._edge(m.id, Rel.HAS, k)
        for k, node in m.steps.items():
            self._node(k, "step", node.name)
        for k, node in m.branches.items():
            self._node(k, "branch", node.name)
        for k, node in m.invariants.items():
            self._node(k, "invariant", node.name, rule=node.rule)
        for k, node in m.meta.items():
            self._node(k, "meta", node.name, kind=node.kind, claim=node.claim, confidence=node.confidence)

        # ownership / containment
        for k, e in m.entities.items():
            for f in e.fields:
                self._edge(k, "has", f)
        for k, a in m.actors.items():
            for p in a.permissions:
                self._edge(k, Rel.GRANTS, p)
        for k, s in m.surfaces.items():
            for c in s.components:
                self._edge(k, Rel.CONTAINS, c)
            if s.presents:
                self._edge(k, Rel.PRESENTS, s.presents)
            for mc in s.states:
                self._edge(k, Rel.HAS_STATE, mc)
        for k, c in m.components.items():
            if c.presents:
                self._edge(k, Rel.PRESENTS, c.presents)
            for iv in c.invokes:
                self._edge(k, Rel.INVOKES, iv)
            for mc in c.states:
                self._edge(k, Rel.HAS_STATE, mc)
            for ch in c.children:
                self._edge(k, Rel.CONTAINS, ch)
        for k, it in m.interactions.items():
            if it.target:
                self._edge(it.target, Rel.HAS_INTERACTION, k)
            if it.invokes:
                self._edge(k, Rel.INVOKES, it.invokes)
        for k, mc in m.machines.items():
            for s in mc.states:
                self._edge(k, "contains", s)
            if mc.owner:
                self._edge(mc.owner, Rel.HAS_STATE, k)
        for k, t in m.transitions.items():
            if t.source:
                self._edge(t.source, Rel.TRANSITIONS_TO, k, target=t.target)
            # event -> transition (§11)
            for eid, ev in m.events.items():
                if ev.name.lower() == (t.event or "").lower():
                    self._edge(eid, Rel.TRIGGERS, k)
        for k, c in m.capabilities.items():
            for p in c.requires:
                self._edge(k, Rel.REQUIRES, p)
            for e in c.consumes:
                self._edge(k, Rel.CONSUMES, e)
            for e in c.produces:
                self._edge(k, Rel.PRODUCES, e)
            for f in c.mutates:
                self._edge(k, Rel.MUTATES, f)
            for e in c.emits:
                self._edge(k, Rel.EMITS, e)
            # capability causes transitions whose event matches its name or an emitted event (§11)
            for tid, t in m.transitions.items():
                if (t.event or "").lower() in {c.name.lower()} | {m.events[e].name.lower() for e in c.emits if e in m.events}:
                    self._edge(k, Rel.CAUSES, tid)
        for k, f in m.flows.items():
            if f.actor:
                self._edge(f.actor, Rel.STEPPED_AS, k)
            if f.goal:
                self._edge(k, Rel.ACHIEVES, f.goal)
                self._edge(f.goal, Rel.ACHIEVED_BY, k)
            if f.entry:
                self._edge(k, Rel.STARTED_AT, f.entry)
            for s in f.steps:
                self._edge(k, "contains", s)
        for k, s in m.steps.items():
            if s.from_:
                self._edge(k, Rel.LEADS_TO, s.from_, via="from")
            if s.action:
                self._edge(k, Rel.INVOKES, s.action)
            if s.to:
                self._edge(k, Rel.LEADS_TO, s.to, via="to")
        for k, b in m.branches.items():
            if b.from_:
                self._edge(k, Rel.BRANCHED_FROM, b.from_)
            for guard, target in b.cases:
                self._edge(k, Rel.LEADS_TO, target, guard=guard)
        for k, inv in m.invariants.items():
            if inv.scope:
                self._edge(k, Rel.GOVERNED_BY, inv.scope)
            for mid, mn in m.meta.items():
                if mn.kind == "requirement":
                    self._edge(mid, Rel.EVIDENCED_BY, k)
        for k, mn in m.meta.items():
            for ev in mn.evidence:
                self.g.add_node(f"evidence.{ev}", payload=Node(id=f"evidence.{ev}", kind="evidence", name=ev))
                self._edge(k, Rel.EVIDENCED_BY, f"evidence.{ev}")

    # ---------- traversal (§15) ----------
    def out(self, id_: str, rel: str | None = None) -> list[str]:
        if id_ not in self.g:
            return []
        if rel is None:
            return list(self.g.successors(id_))
        return [t for _, t, d in self.g.out_edges(id_, data=True) if d.get("rel") == rel]

    def inc(self, id_: str, rel: str | None = None) -> list[str]:
        if id_ not in self.g:
            return []
        if rel is None:
            return list(self.g.predecessors(id_))
        return [s for s, _, d in self.g.in_edges(id_, data=True) if d.get("rel") == rel]

    def rels(self, id_: str) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for _, t, d in self.g.out_edges(id_, data=True):
            out.setdefault(d.get("rel", "?"), []).append(t)
        return out

    def kind(self, id_: str) -> str:
        p = self.g.nodes.get(id_, {}).get("payload")
        return p.kind if p else kind_of(id_)

    def name(self, id_: str) -> str:
        p = self.g.nodes.get(id_, {}).get("payload")
        return p.name if p else id_

    def reverse_rel(self, rel: str) -> str | None:
        """Map an outgoing relation to the relation that points back at the node."""
        back = {Rel.INVOKES: Rel.HAS_INTERACTION, Rel.HAS_INTERACTION: "invokes",
                Rel.REQUIRES: "granted-to", Rel.GRANTS: "requires",
                Rel.EMITS: "triggered-by", Rel.TRIGGERS: "emitted-by",
                Rel.MUTATES: "mutated-by", Rel.CONSUMES: "consumed-by",
                Rel.PRODUCES: "produced-by", Rel.TRANSITIONS_TO: "transitions-from",
                Rel.ACHIEVED_BY: "achieves", Rel.ACHIEVES: "achieved-by",
                Rel.CONTAINS: "contained-by", Rel.HAS_STATE: "state-of",
                Rel.PRESENTS: "presented-by", Rel.EVIDENCED_BY: "evidences"}
        return back.get(rel)


def build_graph(model: Model) -> Graph:
    return Graph(model)
