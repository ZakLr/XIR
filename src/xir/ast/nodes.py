"""Syntax AST (§3) — what the parser literally found. Not the source of truth.

Kept deliberately flat: no IDs are derived here, relationships stay as written,
so `semantic/normalize.py` owns all identity and resolution decisions.
"""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Prov:
    source: str = ""
    reference: str = ""
    confidence: str = "unknown"
    evidence: list[str] = field(default_factory=list)

@dataclass
class Entity:
    name: str
    id: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    provenance: Prov = field(default_factory=Prov)

@dataclass
class Capability:
    name: str
    id: str = ""
    input: dict[str, str] = field(default_factory=dict)
    output: str = ""
    requires: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    mutates: list[str] = field(default_factory=list)
    emits: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)  # legacy free text, upgraded on normalize
    confirmation: bool = False
    audit: bool = False
    provenance: Prov = field(default_factory=Prov)

@dataclass
class Surface:
    name: str
    id: str = ""
    presents: str = ""
    components: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    provenance: Prov = field(default_factory=Prov)

@dataclass
class Flow:
    name: str
    id: str = ""
    goal: str = ""
    actor: str = ""
    entry: str = ""
    steps: list["FlowStep"] = field(default_factory=list)
    branches: list["FlowBranch"] = field(default_factory=list)
    provenance: Prov = field(default_factory=Prov)

@dataclass
class FlowStep:
    name: str
    id: str = ""
    from_: str = ""
    action: str = ""
    to: str = ""

@dataclass
class FlowBranch:
    name: str
    id: str = ""
    from_: str = ""
    cases: list[tuple[str, str]] = field(default_factory=list)

@dataclass
class Goal:
    name: str
    id: str = ""
    description: str = ""
    actor: str = ""

@dataclass
class Actor:
    name: str
    id: str = ""
    permissions: list[str] = field(default_factory=list)

@dataclass
class Permission:
    name: str
    id: str = ""
    description: str = ""

@dataclass
class Event:
    name: str
    id: str = ""

@dataclass
class Component:
    name: str
    id: str = ""
    presents: str = ""
    invokes: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

@dataclass
class Interaction:
    name: str
    id: str = ""
    trigger: str = "click"
    target: str = ""
    invokes: str = ""

@dataclass
class Machine:
    name: str
    id: str = ""
    initial: str = ""
    states: dict[str, "StateDecl"] = field(default_factory=dict)

@dataclass
class StateDecl:
    name: str
    id: str = ""
    transitions: list["TransDecl"] = field(default_factory=list)

@dataclass
class TransDecl:
    event: str = ""
    target: str = ""
    guard: str = ""
    action: str = ""

@dataclass
class Invariant:
    rule: str
    id: str = ""
    scope: str = ""

@dataclass
class Meta:
    kind: str  # requirement | observation | decision | assumption | inference | proposal
    name: str = ""
    id: str = ""
    claim: str = ""
    confidence: str = "unknown"
    evidence: list[str] = field(default_factory=list)

@dataclass
class Experience:
    name: str
    id: str = ""
    goal: str = ""
    version: str = ""
    actors: list[Actor] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)
    permissions: list[Permission] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    components: list[Component] = field(default_factory=list)
    interactions: list[Interaction] = field(default_factory=list)
    machines: list[Machine] = field(default_factory=list)
    invariants: list[Invariant] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    flows: list[Flow] = field(default_factory=list)
    meta: list[Meta] = field(default_factory=list)
