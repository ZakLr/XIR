# XIR Full Vertical Design — 2026-09-27

Source: `PROMPT.md` (2505 lines). Intent: build project from prompt.
Stack: Python package. Scope: full deliverables (Sec 52).

## 1. Architecture

Compiler pipeline (PROMPT Sec 28):

```text
Source DSL (.xir)
  -> Lark lexer/parser
  -> AST (dataclasses)
  -> Canonical Semantic Graph (Pydantic + NetworkX)
  -> Validation
  -> Query / Patch / Diff
  -> Target compilers (HTML, React, A2UI, tests/docs)
```

Graph over tree (Sec 29). AST for syntax. Graph for refs, flows, provenance, mappings.

## 2. Components / Layout

Adapted Sec 36 for Python:

```text
/
├── pyproject.toml
├── README.md / LICENSE / CONTRIBUTING.md
├── DECISIONS.md / OPEN_QUESTIONS.md / RESEARCH.md
├── spec/ontology.md grammar.md semantics.md validation.md queries.md patches.md provenance.md versioning.md
├── research/landscape.md competitors.md related-systems.md differentiation.md benchmarks.md
├── examples/todo/ project-manager/ ecommerce/ dashboard/ (each: app.xir + expected/)
├── src/xir/
│   ├── parser/ (Lark grammar)
│   ├── ast/
│   ├── semantic/ (graph, ids, L0-L6 slicing)
│   ├── validator/
│   ├── query/ + inspect/trace/explain
│   ├── patch/ + diff/
│   ├── compiler/html/ react/ a2ui/ tests_gen/ docs_gen/
│   └── cli/ (Click: parse validate query inspect diff compile test)
├── tests/
└── benchmarks/tasks/ harness.py metrics.py (20 tasks Sec 32 + reconstruction Sec 33 + round-trip Sec 34)
```

Modular (Sec 49). Core without compilers importable.

## 3. Ontology Core

Minimal core hypothesis (Sec 6): Concept, Capability, Surface, State, Flow.
Full investigation set Sec 5 (Experience/Goal/Actor/Entity/Capability/Action/Surface/State/Flow/Constraint/Invariant/Permission/DesignToken/Decision/Provenance/Mapping...).
Each primitive: definition, fields, relations, defaults, validation, examples, anti-examples, core vs extension.
Separate grammar / ontology / semantics (Sec 46).
Mandatory: requirement vs observation vs inference vs proposal (Sec 21), provenance + confidence (Sec 22), uncertainty states (Sec 24), invariants machine-checkable (Sec 20), permissions/roles/audit (Sec 25). No arbitrary code exec.

## 4. Data Flow / IDs / Queries

Stable IDs: `surface.dashboard`, `capability.project.create`, `flow.project.creation` (Sec 9).
Multi-resolution L0-L6: summary → experience → capability/flow → surface → component → state → implementation (Sec 8).
Query slicing: by flow/surface/capability/component with includes (layout, interactions, states, callers, permissions, effects).
Patch ops: add/remove/replace/modify/move/rename/deprecate (Sec 10). Small patches, no full regen.
Semantic diff on identity: added capability, changed surface/interaction/flow/invariant (Sec 11).

## 5. State / Flows / Capabilities / UI

States first-class with transitions, validation for unreachable/dead-end/missing (Sec 12, statecharts).
Flows = user goals with actors, preconditions, branches, errors/retries/cancellation (Sec 13).
Capabilities > controls; one capability → button/menu/shortcut/palette/voice/tool/API (Sec 14).
UI semantic: surfaces/regions/components/layout relationships, not pixels (Sec 15). Layout constraints not CSS (Sec 16, Sec 42). Design systems first-class via tokens (Sec 17). Mappings semantic→React/Figma/A2UI/MCP-tool/API (Sec 18). Accessibility derived (Sec 19). Distinguish semantic vs visual component e.g. Collection → Table/List/Grid (Sec 41).

## 6. Validation / Error Handling

Validator first-class (Sec 47): undefined refs, duplicate IDs, invalid capabilities/permissions/mappings, unreachable states, dead-end flows, missing transitions/states, circular deps, broken refs.
CLI `validate` fails with stable error codes + IDs. No silent inference → requirement promotion.

## 7. CLI (Sec 37, Click)

```bash
xir parse app.xir
xir validate app.xir
xir query app.xir "flow CreateProject"
xir inspect app.xir surface Dashboard
xir diff old.xir new.xir
xir compile app.xir --target react|html|a2ui
xir test app.xir
```

Agent ops (Sec 27): inspect/query/create/modify/delete/diff/validate/explain/trace/compile/render/test. Reference workflow Sec 40: query → identify concepts/capabilities/surfaces/flows/states → check invariants → propose patch → validate → apply → compile → test → provenance → diff.

## 8. Testing / Benchmarks

pytest unit (parser, graph, validator, query, patch, diff, compilers) + CLI e2e + example goldens.
Benchmark suite Sec 32: ≥20 tasks (CRUD, states, nav, search, permissions, layout change, explain, unreachable/missing detection).
Compare: prose vs JSON vs source vs screenshots vs XIR. Metrics: tokens, context size, tool calls, completion, correctness, state/flow fidelity, UI fidelity, a11y, regressions, time.
Flagship reconstruction Sec 33: model → hide source → reconstruct → measure semantic/behavior/flow/visual/a11y/edge fidelity. Round-trip Sec 34: DSL→impl→extractor→DSL semantic stability; define equivalence.
V0 gate Sec 35/51/56: A/B same tasks with/without XIR; must show fewer tokens, fewer mistakes, fewer retrievals, better fidelity before expanding.

## 9. Research (Phase 1, before code freeze)

Deliver `research/`: landscape, competitors, related-systems, design-principles, open-problems, differentiation. Per system (UML/SysML/BPMN, HTML/CSS/ARIA/A2UI/Adaptive Cards, MCP/AG-UI, Figma/Code Connect/tokens, OpenAPI/JSON Schema/Protobuf, AST/IR/tree-sitter, RDF/OWL/JSON-LD/graphs): problem, abstraction, strengths/weaknesses, format, agent relevance, overlap/difference, integrate vs avoid. Primary sources. No unsupported claims.

## 10. Order (Sec 59)

1 Research → 2 Ontology v0.1 → 3 challenge vs 5 real apps → 4 minimal grammar → 5 graph v0.1 → 6 parser+validator+query → 7 examples (project-manager complete Sec 38/39 first, then todo/ecommerce/dashboard) → 8 benchmark → 9 measure → 10 compiler targets (HTML → tests → React → A2UI).
Maintain DECISIONS.md / OPEN_QUESTIONS.md / RESEARCH.md every phase. Research→experiment→measure→decide. Self-criticism checklist Sec 53 each decision. Strategic constraint Sec 54: connect HTML/CSS/Figma/A2UI/MCP/OpenAPI, not compete.

## 11. Open Questions

- Lark vs tree-sitter for incremental parsing?
- Pydantic v2 + NetworkX vs RDF-lib for graph/queries?
- Interchange: JSON dump vs CBOR for agent retrieval?
- Versioning/migration syntax v0.1 scope?

---
Self-review: no TBDs, sections consistent with PROMPT Sec 28/35/49/52/55, single full-vertical scope, no ambiguous requirements beyond Q11 flagged.
