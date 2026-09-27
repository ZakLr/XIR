# Semantics

`spec/grammar.md` defines syntax; `spec/ontology.md` defines concepts; this file defines meaning.

- Experience: root product intent; children linked by stable IDs (`surface.dashboard`,
  `capability.project.create`, `flow.project.creation`).
- Entity: domain type; attributes are `name: TypeExpr`, `TypeExpr := NameBracket ("|" NameBracket)*`.
- Capability: invocable effect; input/output typed; requires = permission refs; effects = state
  assignments; destructive ones require confirmation (validated).
- Surface: presents an entity (optionally collection `X[]`); components listed; states enumerated.
- Flow: user goal; actor must be declared; steps are `A -> B` edges flattened to ordered list;
  unknown steps flagged unless matching surface/capability/entity/flow or control vocabulary.
- Graph: AST → `semantic/graph.py` NetworkX DiGraph; `summarize(exp, L0–L3)` projection.
- Equivalence: two models equal iff `diff()` reports "no semantic changes" (identity-based, Sec 11).
