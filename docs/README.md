# Documentation

## Start here

| I want to… | Read |
|---|---|
| **use XIR (as an agent or a developer)** | **[AGENTS.md](AGENTS.md)** — the command surface, traversal recipes, patch workflow, conventions |
| **understand this repository** | **[REPO.md](REPO.md)** — layout, how to run it, where to start reading, how to contribute |
| understand the product | [README](../README.md) |
| understand what v0.2 could not express | [docs/v0.3-audit.md](v0.3-audit.md) |

## Specification

The language has three separate layers, on purpose.

| Doc | Defines |
|---|---|
| [spec/grammar.md](../spec/grammar.md) | syntax — what the parser accepts |
| [spec/ontology.md](../spec/ontology.md) | concepts — what the primitives are |
| [spec/semantics.md](../spec/semantics.md) | meaning — identity, resolution, equivalence |
| [spec/semantic-graph.md](semantic-graph.md) | node types, edge types, normalization, traversal |

## Using it

| Doc | Covers |
|---|---|
| [spec/queries.md](../spec/queries.md) | `show`, `trace`, `follow`, `who-can`, `affected`, context levels |
| [spec/patches.md](../spec/patches.md) | atomic transactions, rename, guarded removal |
| [spec/validation.md](../spec/validation.md) | every finding code and when it fires |
| [spec/provenance.md](../spec/provenance.md) | sources, confidence, evidence |
| [spec/versioning.md](../spec/versioning.md) | model evolution |

## Background

- [research/landscape.md](../research/landscape.md) — the problem and the gap
- [research/related-systems.md](../research/related-systems.md) — UML, A2UI, MCP, Figma, ASTs, RDF and how they relate
- [research/competitors.md](../research/competitors.md) — nearest approaches and why they fall short
- [research/differentiation.md](../research/differentiation.md) — the semantic layer that connects them
- [research/design-principles.md](../research/design-principles.md) — the twelve rules the design follows
- [research/open-problems.md](../research/open-problems.md) — what is still unsolved
- [research/benchmarks.md](../research/benchmarks.md) — how the benchmark works

## Project process

- [DECISIONS.md](../DECISIONS.md) — architectural decisions and their reasons
- [OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md) — open questions and known gaps
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to propose a change
- [RELEASING.md](../RELEASING.md) — release and publish steps
- [CHANGELOG.md](../CHANGELOG.md) — release history
- [benchmarks/report.md](../benchmarks/report.md) — measured results, with provenance labels
