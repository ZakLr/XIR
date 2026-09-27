"""Semantic IR (§3) — the source of truth for graph, validation, query, patch, compile.

Parser produces syntax AST; `semantic/normalize.py` turns AST into these models.
Nothing downstream may depend on parser structures.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from xir.ir.ids import make_id, kind_of, valid_id, KINDS

# Typed relations (§13). Every edge in the graph uses one of these.
class Rel:
    HAS = "has"
    ACHIEVED_BY = "achieved-by"
    ENABLED_BY = "enabled-by"
    EXPOSED_BY = "exposed-by"
    GRANTS = "grants"
    REQUIRES = "requires"
    CONSUMES = "consumes"
    PRODUCES = "produces"
    MUTATES = "mutates"
    EMITS = "emits"
    CAUSES = "causes"
    TRIGGERS = "triggers"
    TRANSITIONS_TO = "transitions-to"
    CONTAINS = "contains"
    PRESENTS = "presents"
    INVOKES = "invokes"
    HAS_STATE = "has-state"
    HAS_INTERACTION = "has-interaction"
    STARTED_AT = "starts-at"
    ACHIEVES = "achieves"
    STEPPED_AS = "stepped-as"
    BRANCHED_FROM = "branched-from"
    LEADS_TO = "leads-to"
    GOVERNED_BY = "governed-by"
    EVIDENCED_BY = "evidenced-by"

CONFIDENCE = ("confirmed", "probable", "inferred", "tentative", "proposed", "deprecated", "unknown")
SOURCES = ("human", "requirement-document", "code", "design", "API", "test",
           "analytics", "screenshot", "inference", "agent", "proposal")

class Provenance(BaseModel):
    """Structured evidence, not bare metadata (§20)."""
    source: str | None = None
    reference: str | None = None
    confidence: str = "unknown"
    evidence: list[str] = Field(default_factory=list)

    def ok(self) -> bool:
        return (self.source is None or self.source in SOURCES) and self.confidence in CONFIDENCE

class Base(BaseModel):
    id: str
    name: str
    provenance: Provenance = Field(default_factory=Provenance)

class Goal(Base):
    description: str = ""
    actor: str | None = None

class Actor(Base):
    permissions: list[str] = Field(default_factory=list)

class Permission(Base):
    description: str = ""

class Field_(Base):
    type: str = "Text"

class Entity(Base):
    fields: list[str] = Field(default_factory=list)  # field ids

class Event(Base):
    pass

class Capability(Base):
    input: dict[str, str] = Field(default_factory=dict)   # param -> type name
    output: str | None = None
    requires: list[str] = Field(default_factory=list)      # permission ids
    consumes: list[str] = Field(default_factory=list)      # entity ids
    produces: list[str] = Field(default_factory=list)      # entity ids
    mutates: list[str] = Field(default_factory=list)       # field ids
    emits: list[str] = Field(default_factory=list)         # event ids
    confirmation: bool = False
    audit: bool = False

class State(Base):
    initial: bool = False

class Transition(Base):
    source: str = ""      # state id
    event: str = ""       # event or trigger name
    target: str = ""      # state id
    guard: str | None = None
    action: str | None = None

class Machine(Base):
    initial: str | None = None        # state id
    initial_declared: bool = False    # False means the initial state was inferred
    states: list[str] = Field(default_factory=list)
    transitions: list[str] = Field(default_factory=list)  # transition ids
    owner: str | None = None          # surface or component id

class Component(Base):
    presents: str | None = None                 # entity id
    invokes: list[str] = Field(default_factory=list)   # capability ids
    states: list[str] = Field(default_factory=list)    # machine id
    children: list[str] = Field(default_factory=list)  # component ids
    legacy: bool = False   # synthesized from a flat `components { A B }` list (§31)

class Interaction(Base):
    trigger: str = "click"
    target: str | None = None      # component id
    invokes: str | None = None     # capability id
    states: list[str] = Field(default_factory=list)  # machine ids

class Surface(Base):
    presents: str | None = None
    components: list[str] = Field(default_factory=list)  # component ids
    states: list[str] = Field(default_factory=list)       # machine id

class Step(Base):
    from_: str | None = None
    action: str | None = None
    to: str | None = None

class Branch(Base):
    from_: str | None = None
    cases: list[tuple[str, str]] = Field(default_factory=list)  # (guard, target)

class Flow(Base):
    goal: str | None = None
    actor: str | None = None
    entry: str | None = None
    steps: list[str] = Field(default_factory=list)    # step ids
    branches: list[str] = Field(default_factory=list)  # branch ids

class Invariant(Base):
    rule: str = ""
    scope: str | None = None

class Meta(Base):
    """requirement | observation | decision | assumption | inference | proposal."""
    kind: str = "proposal"
    claim: str = ""
    confidence: str = "unknown"
    evidence: list[str] = Field(default_factory=list)

class Model(BaseModel):
    """Canonical semantic model. Root of everything downstream."""
    id: str
    name: str
    goal: str = ""                 # free-text product goal (kept for back-compat)
    version: str = ""
    goals: dict[str, Goal] = Field(default_factory=dict)
    actors: dict[str, Actor] = Field(default_factory=dict)
    permissions: dict[str, Permission] = Field(default_factory=dict)
    entities: dict[str, Entity] = Field(default_factory=dict)
    fields: dict[str, Field_] = Field(default_factory=dict)
    events: dict[str, Event] = Field(default_factory=dict)
    capabilities: dict[str, Capability] = Field(default_factory=dict)
    surfaces: dict[str, Surface] = Field(default_factory=dict)
    components: dict[str, Component] = Field(default_factory=dict)
    interactions: dict[str, Interaction] = Field(default_factory=dict)
    machines: dict[str, Machine] = Field(default_factory=dict)
    states: dict[str, State] = Field(default_factory=dict)
    transitions: dict[str, Transition] = Field(default_factory=dict)
    flows: dict[str, Flow] = Field(default_factory=dict)
    steps: dict[str, Step] = Field(default_factory=dict)
    branches: dict[str, Branch] = Field(default_factory=dict)
    invariants: dict[str, Invariant] = Field(default_factory=dict)
    meta: dict[str, Meta] = Field(default_factory=dict)
    # references written in source that could not be resolved. Kept out of the graph
    # (so it holds no phantom nodes) but reported by the validator.
    unresolved: list[dict] = Field(default_factory=list)

    # ---------- identity / lookup ----------
    _buckets: dict = {}

    def bucket(self, kind: str) -> dict:
        return {
            "goal": self.goals, "actor": self.actors, "permission": self.permissions,
            "entity": self.entities, "field": self.fields, "event": self.events,
            "capability": self.capabilities, "surface": self.surfaces,
            "component": self.components, "interaction": self.interactions,
            "machine": self.machines, "state": self.states, "transition": self.transitions,
            "flow": self.flows, "step": self.steps, "branch": self.branches,
            "invariant": self.invariants, "meta": self.meta,
        }.get(kind, {})

    def get(self, id_: str):
        if id_ == self.id:
            return self
        if not valid_id(id_):
            return None
        return self.bucket(kind_of(id_)).get(id_)

    def resolve(self, ref: str) -> str | None:
        """Accept an explicit ID, or a bare/partial name, and return the canonical ID (§31).

        Ambiguity is broken by preferring the shallowest ID, so a bare name picks the
        primary concept rather than a nested detail node that shares its label.
        """
        if not ref:
            return None
        if valid_id(ref) and self.get(ref) is not None:
            return ref
        ref_l = ref.lower()
        # `flow.AddTodo` / `capability.archiveProject` — a kind prefix plus a name
        if "." in ref:
            head, tail = ref.split(".", 1)
            if head in KINDS:
                for i in self.bucket(head):
                    n = self.bucket(head)[i]
                    if n.name == tail or n.name.lower() == tail.lower():
                        return i
                for i in self.bucket(head):
                    if i.split(".")[-1].lower() == tail.lower():
                        return i
        # exact name match, then case-insensitive, then id-suffix — shallowest wins
        for pred in (lambda n: n == ref, lambda n: n.lower() == ref_l):
            hits = [i for i in self.all_ids() if self._name_of(i) == ref or pred(self._name_of(i))]
            if hits:
                return self._shallowest(hits)
        hits = [i for i in self.all_ids() if i.split(".")[-1].lower() == ref_l]
        if hits:
            return self._shallowest(hits)
        return None

    @staticmethod
    def _shallowest(hits: list[str]) -> str:
        return sorted(hits, key=lambda i: (i.count("."), len(i), i))[0]

    def _name_of(self, id_: str) -> str:
        n = self.get(id_)
        return n.name if n is not None else id_

    def all_ids(self) -> list[str]:
        out = [self.id]
        for kind, bucket in self.buckets().items():
            out.extend(bucket.keys())
        return out

    def buckets(self) -> dict[str, dict]:
        return {
            "goal": self.goals, "actor": self.actors, "permission": self.permissions,
            "entity": self.entities, "field": self.fields, "event": self.events,
            "capability": self.capabilities, "surface": self.surfaces,
            "component": self.components, "interaction": self.interactions,
            "machine": self.machines, "state": self.states, "transition": self.transitions,
            "flow": self.flows, "step": self.steps, "branch": self.branches,
            "invariant": self.invariants, "meta": self.meta,
        }

    def remove(self, id_: str) -> None:
        if id_ == self.id:
            raise ValueError("cannot remove the experience root")
        self.bucket(kind_of(id_)).pop(id_, None)

    def rename(self, id_: str, new_name: str, new_id: str | None = None) -> str:
        """Rename a node. Identity is preserved when new_id keeps the same segments (§4)."""
        if id_ == self.id:
            self.name = new_name
            return id_
        kind = kind_of(id_)
        bucket = self.bucket(kind)
        node = bucket.pop(id_)
        target = new_id or id_
        node.name = new_name
        bucket[target] = node
        return target
