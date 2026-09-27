# Design principles (distilled)

1. Semantics before presentation: capability/action first, button/onClick never in core.
2. UI is a projection: one model → React/HTML/A2UI/Figma/docs/tests/a11y/analytics/tools.
3. Framework independence: no React/CSS/LLM-vendor concepts in core; adapters only.
4. Agent-first: dense, deterministic, retrievable, diffable, patchable, low-token; readability second.
5. Human-authorable: concise DSL, never raw JSON as source.
6. Minimal core, justified primitives: Concept/Capability/Surface/State/Flow + extensions only with proof.
7. Defaults carry semantics: `Button` implies role/focus; efficiency via ontology, not cryptic abbreviations.
8. Multi-resolution + stable IDs: L0–L6 slicing; identity survives formatting.
9. Explicit uncertainty + provenance: requirement/observation/inference never conflated; confidence tagged.
10. Invariants machine-checkable; destructive acts need confirmation + audit.
11. Connect, don't compete: OpenAPI/MCP/A2UI/Figma/ARIA are targets, not rivals.
12. Measure or remove: every feature must move tokens/mistakes/retrievals/fidelity (Sec 53 gate).
