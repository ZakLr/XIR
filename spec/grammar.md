# Grammar (v0.3)

Grammar: `src/xir/parser/grammar.lark`. Parser: `src/xir/parser/strict.py`.

## Parser choices

- **Earley, not LALR.** The grammar has intentional overlap between legacy flat forms
  and explicit blocks. LALR resolves that by silently dropping alternatives, which
  turns valid XIR into a parse error. Earley also forbids embedded transformers, so
  the tree is built first and transformed afterwards.
- **One named rule per alternative.** Lark filters anonymous literal tokens out of rule
  callbacks, so a rule like `a: X y | z | w` cannot report which alternative matched.
  Every alternative that must be distinguished gets its own rule.
- **`LINE`/`PROVVAL` refuse to start at a quote**, otherwise they out-compete
  `ESCAPED_STRING` on quoted values.

## Strictness

`xir parse` and every command are strict. Invalid XIR raises `ParseError` with a line and
column. There is no silent fallback to a tolerant parse.

```text
$ xir parse broken.xir
ERROR: invalid XIR: invalid XIR at line 4, column 12: ...
```

`xir recover` is the explicit best-effort mode. It drops declarations that do not parse,
reports every unresolved reference and every inference, and never invents semantics.

## Legacy compatibility

These forms still parse and are upgraded during normalization:

| Legacy | Normalized to |
|---|---|
| `actors { a b }` | `actor` declarations |
| `components { A B }` | `component` nodes marked `legacy` |
| `states: a b c` | a `machine` with states and no transitions |
| `A -> B` in a flow | an explicit `step` with from/to |
| `effects: x.y = z` | `mutates: [field.x.y]` |
| `step: Surface` | a step with only a target |

## Declaration forms

```text
goal createProject { description: "..."  actor: member }
permission project.archive { description: "..." }
actor manager { permissions { project.read project.archive } }
event ProjectArchived
capability archiveProject { input { project: Project }  output: Project
                            requires: project.archive  consumes: Project
                            mutates { Project.status }  emits: ProjectArchived
                            confirmation: required  audit: required }
interaction archiveProject { trigger: click  target: component...  invokes: archiveProject }
component ArchiveButton { id: ...  presents: Project  invokes: archiveProject }
state projectList { initial: loading  loading { on dataReceived -> populated } }
surface Dashboard { presents: Project[]  components { ... }  machine: projectList }
flow CreateProject { goal: createProject  actor: member  entry { surface: surface.dashboard }
                     step openForm { from: ...  action: interaction.createProject  to: ... }
                     branch validation { from: ...  success -> entity.project } }
invariant destructiveActions { rule: "..."  scope: capability.archiveProject }
inference archiveLocation { claim: "..."  confidence: probable  evidence { screenshot.x } }
```

`id:` may be written inside a declaration block to pin a semantic id explicitly.
