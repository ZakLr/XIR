"""AST nodes — dataclasses, syntax-level."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Entity:
    name: str
    attrs: dict[str, str] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)

@dataclass
class Capability:
    name: str
    input: dict[str, str] = field(default_factory=dict)
    output: str = ""
    requires: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    confirmation: bool = False
    audit: bool = False
    provenance: dict[str, str] = field(default_factory=dict)

@dataclass
class Surface:
    name: str
    presents: str = ""
    components: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)

@dataclass
class FlowStep:
    name: str

@dataclass
class Flow:
    name: str
    actor: str = ""
    steps: list[str] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)

@dataclass
class Meta:
    kind: str  # requirement | observation | decision | assumption | inference | proposal
    text: str = ""
    provenance: dict[str, str] = field(default_factory=dict)

@dataclass
class Experience:
    name: str
    goal: str = ""
    version: str = ""
    actors: list[str] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    surfaces: list[Surface] = field(default_factory=list)
    flows: list[Flow] = field(default_factory=list)
    meta: list[Meta] = field(default_factory=list)
