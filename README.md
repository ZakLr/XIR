# XIR — the semantic IR for interactive products

> Model intent, capabilities, surfaces, state and flows once.
> Compile to UI, tests, docs and agent tools.

XIR answers agent questions by **traversing typed semantic relationships**, not by
matching strings. This is the whole design:

```text
$ xir trace examples/project-manager/app.xir archiveProject
CAPABILITY: archiveProject
  REQUIRES: project.archive      [permission.project.archive]
  MUTATES:  status               [field.project.status]
  EMITS:    ProjectArchived      [event.projectArchived]
  EXPOSED BY: ArchiveButton      [component.projectDetail.archiveButton]
  STATE:   confirming            [state.projectDetailActions.confirming]
```

## Why

An interactive product lives as disconnected artifacts: code, screenshots, Figma,
prose, schemas. An agent reading all of that burns tokens, guesses at intent, and
cannot tell a *relationship* from a *coincidence of words*.

XIR is a compiler-grade intermediate representation. You author semantics; the model
projects to React, HTML, A2UI, docs, accessibility metadata and Playwright tests.

## Install

```bash
pip install -e .[dev]
pytest
```

## The pipeline

```text
source .xir
  -> strict parse          (invalid XIR raises; it never degrades silently)
  -> syntax AST            (what the file literally says)
  -> normalization         (owns identity and reference resolution)
  -> semantic IR           (the source of truth)
  -> typed graph           (every edge has a relation)
  -> validate / query / patch / diff / compile
```

Nothing downstream of the IR reads the syntax AST.

## What an agent can do

| Question | Command |
|---|---|
| What happens when the user clicks Archive? | `xir trace app.xir archiveProject` |
| What permission is required? | `xir query app.xir "who can archiveProject"` |
| What changes if this field changes? | `xir query app.xir "affected field.project.status"` |
| Where is this implemented in the UI? | `xir follow app.xir capability.archiveProject invokes` |
| Give me a compact slice of this surface | `xir inspect app.xir surface.dashboard` |
| What is wrong with this model? | `xir validate app.xir` |
| Rename it without breaking references | `xir patch app.xir "patch { rename capability.archiveProject to_name: archive }"` |
| Generate the React app | `xir compile app.xir --target react --out src/App.jsx` |
| Generate behaviour tests | `xir compile app.xir --target playwright` |

## Ontology

`Experience` · `Goal` · `Actor` · `Permission` · `Entity` · `Field` · `Event` ·
`Capability` · `Surface` · `Component` · `Interaction` · `Machine` · `State` ·
`Transition` · `Flow` · `Step` · `Branch` · `Invariant` · provenance/evidence

Full definitions in [`spec/ontology.md`](spec/ontology.md); the graph in
[`spec/semantic-graph.md`](spec/semantic-graph.md).

## Stable identity

Names are display. **IDs are identity.**

```text
rename capability.archiveProject to_name: archive
  -> same id, new name, zero reference breakage

rename capability.archiveProject to_id: capability.project.archive
  -> identity change; every reference rewritten atomically, or the patch rolls back
```

## Safety

A patch is a transaction: resolve → apply → validate → commit or rollback. It never
leaves a partially invalid model, and `remove` refuses while anything still points at
the target.

## Examples

| Example | Shows |
|---|---|
| `examples/project-manager` | the full ontology: goals, permissions, actors, events, state machines, interactions, invariants, evidence |
| `examples/clinic` | a domain extension (healthcare) |
| `examples/ecommerce` | confirmation and permissions |
| `examples/todo` | the minimal core |
| `examples/dashboard` | states and a refresh flow |

Each ships `app.xir` plus `expected.{xir,html,react,a2ui,docs,a11y,playwright}` goldens.

## Benchmarks

`python benchmarks/tasks.py` runs retrieval, reasoning, UI, state, adversarial and
modification tasks, plus a context-cost report. Results are labelled
**MEASURED**, **SIMULATED** or **INFERRED** — see
[`benchmarks/report.md`](benchmarks/report.md). Simulated retrieval counts are *not*
agent performance and are never presented as such.

## Documentation

- **[docs/AGENTS.md](docs/AGENTS.md)** — using XIR: command surface, traversal recipes, patch workflow, conventions
- **[docs/REPO.md](docs/REPO.md)** — this repository: layout, how to run it, how to contribute
- [docs/index](docs/README.md) — the rest: spec, research, process
- [docs/v0.3-audit.md](docs/v0.3-audit.md) — what v0.2 could not express, and why
- [`spec/`](spec/) — grammar, semantics, ontology, graph, queries, patches, validation

## Status

v0.3. The semantic model is the product; parsing and rendering are deliberately
secondary. Known gaps are tracked in `OPEN_QUESTIONS.md`.

## Agent skill

`skills/xir/` is a ready-to-install agent skill: trigger-rich frontmatter, five
reference files, and a model-health script.

```bash
cp -r skills/xir ~/.config/opencode/skills/     # or ~/.claude/skills/
```

```bash
$ python skills/xir/scripts/xir_health.py examples/project-manager/app.xir
  ProjectManager [exp.projectManager] v1
  coverage:
    capabilities_typed                 2/2
    machines_with_transitions          3/3
    flow_steps_fully_specified         2/2
  round-trip: stable
  findings: none
```

The health report shows the distinction that matters: a model can validate clean and
still be barely specified. That gap is what the coverage lines expose.

## License

AGPLv3+.
