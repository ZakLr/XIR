<p align="center">
  <img src="docs/logo.svg" width="96" alt="XIR logo"/>
</p>

<h1 align="center">XIR — the semantic IR for interactive products</h1>

<p align="center">
  Model intent, capabilities, surfaces, state and flows once.
  Compile to UI, tests, docs and agent tools.
</p>

<p align="center">
  <a href=".github/workflows/ci.yml"><img src="https://img.shields.io/badge/ci-passing-brightgreen" alt="CI"/></a>
  <img src="https://img.shields.io/badge/license-AGPLv3%2B-blue" alt="AGPLv3+"/>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/version-1.0.0-purple" alt="1.0.0"/>
</p>

> One-liner: XIR is a compiler-grade semantic layer for apps — agents query slices of the
> product model instead of drowning in code, screenshots and prose.

## Quickstart

```bash
pip install -e .[dev]
pytest                                   # 14 tests
xir parse examples/project-manager/app.xir
xir validate examples/project-manager/app.xir
xir compile examples/project-manager/app.xir --target react
xir bench                                # 20-task suite
```

## Examples

| Example | Domain | Highlights |
|---|---|---|
| `examples/project-manager/` | team projects | full ontology, provenance, audit |
| `examples/todo/` | tasks | minimal core |
| `examples/ecommerce/` | shop + checkout | confirmation, permissions |
| `examples/dashboard/` | metrics | states, refresh flow |
| `examples/clinic/` | healthcare extension | version, requirement, cross-domain proof |

Each ships `app.xir` + `expected.{html,react,a2ui,xir,docs,a11y,playwright}` goldens.

## 1. Problem
Interactive products live as disconnected artifacts: code, screenshots, Figma, prose, schemas.
Agents drown in tokens and ambiguity with no shared semantic model.

## 2. Why existing approaches are insufficient
See `research/`: UI frameworks render pixels; API schemas cover data; card formats (A2UI/Adaptive)
cover rendering; MCP covers tool wire; UML covers diagrams. None links intent → capabilities →
surfaces → state → flows → mappings with queries, patches, diffs, provenance.

## 3. Core thesis
A compact semantic IR helps agents do product engineering with fewer tokens, fewer mistakes,
fewer retrievals, better behavioral fidelity than conventional context.

## 4. Ontology
Core: Concept, Capability, Surface, State, Flow (+ Entity/Actor). Full: `spec/ontology.md`,
semantics `spec/semantics.md`, validation `spec/validation.md`, queries `spec/queries.md`,
patches `spec/patches.md`, provenance `spec/provenance.md`, versioning `spec/versioning.md`.

## 5. Syntax
```text
experience ProjectManager {
  goal: "Help teams organize and execute work."
  actors { member manager admin }
  entity Project { id: ID  name: Text  status: draft | active | archived }
  capability archiveProject {
    input { project: Project }
    requires: project.archive
    effects: project.status = archived
    confirmation: required
  }
  surface Dashboard {
    presents: Project[]
    components { Sidebar Main }
    states: loading empty populated error
  }
  flow CreateProject {
    actor: member
    Dashboard -> CreateProject
  }
}
```
Strict Lark grammar + tolerant fallback (`src/xir/parser/`).

## 6. Complete example
`examples/project-manager/app.xir` (+ todo/ecommerce/dashboard/clinic), each with
`expected.{html,react,a2ui,xir,docs,a11y,playwright}` goldens.

## 7. How agents use it
`xir parse|validate|query|inspect|explain|diff|compile|test|bench|patch` — query slices (L0–L6),
trace capabilities, propose patches, validate, diff. Workflow: `spec/patches.md`.

## 8. How it compiles
`Source → Lark → AST → NetworkX graph → validate → query/patch/diff → HTML/React/A2UI/docs/a11y/Playwright`
(`src/xir/compiler/` + `dsl.py` canonical emitter + HTML extractor).

## 9. Benchmark methodology
`benchmarks/tasks.py` (20 tasks), `reconstruct.py` (semantic rebuild), `roundtrip.py`
(DSL→canonical→reparse stability), `baseline.py` (IXL-vs-baselines proxy).
Report: `benchmarks/report.md`.

## 10. Known limitations
Tree-sitter incremental parsing, learned retrieval priorities, formal temporal proofs, and
blinded large-scale agent trials are future work. See OPEN_QUESTIONS.md.

## License
AGPLv3+ — free to use, modify and share; network use (SaaS) must offer source (Sec 13).
See `LICENSE`. Commercial relicensing not offered.
