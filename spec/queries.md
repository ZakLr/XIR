# Queries (v0.3)

Engine: `src/xir/query/engine.py`. Everything is answered from graph edges. The
keyword router survives only to turn a phrase into a reference; the answer itself is
never a string match (`tests/test_semantics.py` asserts the engine uses `g.out`/`g.inc`).

## Operations

| Command | Function | Answers |
|---|---|---|
| `show <ref>` | `Q.show` | the node plus its outgoing typed relations |
| `trace <capability>` | `Q.trace` | input/output/permissions/mutations/events + how it is exposed + affected flows and states |
| `from <id> follow <rel>` | `Q.follow` | structural traversal, optionally `--depth` |
| `who can <capability>` | `Q.who_can` | actors holding the required permission |
| `affected <ref>` | `Q.affected` | everything that changes if this node changes |
| `query <phrase>` | `Q.query` | routes to the above, or lists a bucket |

`show` and `trace` are the high-value agent operations: they return a compact semantic
slice rather than a dump.

## Examples

```text
$ xir trace app.xir archiveProject
CAPABILITY: archiveProject
  ID: capability.archiveProject
  INPUT: project: Project
  REQUIRES: project.archive  [permission.project.archive]
  MUTATES: status  [field.project.status]
  EMITS: ProjectArchived  [event.projectArchived]
  CONFIRMATION: required
  AUDIT: required
  EXPOSED BY: ArchiveButton  [component.projectDetail.archiveButton]
  FLOW: CreateProject  [flow.createProject]
  STATE: confirming  [state.projectDetailActions.confirming]

$ xir follow app.xir capability.archiveProject mutates
FIELD: status  [field.project.status]

$ xir query app.xir "who can archiveProject"
project.archive: manager
```

## Context levels

`xir parse <file> --level N` projects the model at L0..L6 via
`semantic/levels.py`. Every line carries the semantic id it came from, so an agent can
load exactly the slice it needs.
