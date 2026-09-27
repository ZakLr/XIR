# CLI reference

Full command surface with output shapes. `<ref>` accepts an id, a name, or a
kind-qualified name (`archiveProject`, `capability.archiveProject`,
`capability.project.archive`).

## Reading

### `xir parse <f> --level N`

Project the model at detail level 0–6. Start at 0 or 1 and go deeper only when the
question demands it.

```bash
xir parse app.xir --level 0
# ProjectManager v1 [exp.projectManager]: Help teams organize and execute work.
#   2 entities, 2 capabilities, 3 surfaces, 1 flows, 13 states, 21 transitions
```

Default level is 3.

### `xir validate <f>`

Every semantic inconsistency. Exit code 1 if any finding.

```bash
xir validate app.xir
# valid: ProjectManager [exp.projectManager] 81 semantic nodes
```

Finding codes are documented in the XIR repo at `spec/validation.md`. The ones you
will hit most:

| Code | Meaning |
|---|---|
| `UNRESOLVED_REFERENCE` | a reference names something that does not exist |
| `MISSING_INITIAL_STATE` | a machine does not declare `initial:` |
| `UNREACHABLE_STATE` | no path from the initial state reaches it |
| `DEAD_END_STATE` | no outgoing transition |
| `INVALID_TRANSITION_TARGET` | a transition points outside its machine |
| `MISSING_CONFIRMATION` | a destructive capability has no `confirmation` |
| `UNREACHABLE_CAPABILITY` | no actor holds the permission it requires |
| `ORPHAN_COMPONENT` | a component is on no surface |
| `UNSUPPORTED_CONFIDENCE` | an `inference` claims `confirmed` |

### `xir inspect <f> <ref>`

One node and its outgoing relations. The structural slice.

```bash
xir inspect app.xir surface.dashboard
# SURFACE: Dashboard  [surface.dashboard]
#   CONTAINS: ProjectList  [component.dashboard.projectList]
#   PRESENTS: Project  [entity.project]
#   HAS STATE: projectList  [machine.projectList]
```

### `xir trace <f> <capability>`

The behavioural chain. Use this first for any "what does this do" question.

```bash
xir trace app.xir archiveProject
# CAPABILITY: archiveProject
#   ID: capability.archiveProject
#   INPUT: project: Project
#   OUTPUT: Project  [entity.project]
#   REQUIRES: project.archive  [permission.project.archive]
#   CONSUMES: Project  [entity.project]
#   MUTATES: status  [field.project.status]
#   EMITS: ProjectArchived  [event.projectArchived]
#   CONFIRMATION: required
#   AUDIT: required
#   EXPOSED BY: ArchiveButton  [component.projectDetail.archiveButton]
#   EXPOSED BY: archiveProject  [interaction.archiveProject]
#   FLOW: CreateProject  [flow.createProject]
#   STATE: confirming  [state.projectDetailActions.confirming]
```

### `xir follow <f> <ref> <relation> [--depth N]`

Structural traversal by edge relation.

```bash
xir follow app.xir capability.archiveProject emits
# EVENT: ProjectArchived  [event.projectArchived]

xir follow app.xir component.projectDetail.archiveButton invokes --depth 2
```

### `xir query <f> "<phrase>"`

Routed natural language. The router resolves the phrase to a reference; the answer
comes from the graph.

| Phrase | Answers |
|---|---|
| `who can <capability>` | actors holding the required permission |
| `affected <ref>` | everything that changes if this node changes |
| `what happens when the user clicks <x>` | the full trigger chain |
| `show <kind>` | lists that bucket |
| `show <ref>` | same as inspect |
| `trace <ref>` | same as trace |

```bash
xir query app.xir "who can archiveProject"
# project.archive: manager
```

Note `member` is absent. The model knows who may not act without reading a single
`if`.

### `xir recover <f>`

Explicit best-effort parse. Drops declarations that do not parse, then reports every
unresolved reference and every inference. Exit code 1 when recovery was needed.

**Never patch a recovered model without re-validating.**

## Changing

### `xir patch <f> "<patch>"`

Transaction: resolve → apply → validate → commit or roll back.

```text
patch {
  rename <ref> to_name: <name>
  rename <ref> to_id: <id>
  modify <ref> <field>: <value>
  modify <ref> <list_field>:
  add <kind>.<Name> <field>: <value>
  remove <ref>
  deprecate <ref>
  move <ref> to: <index>
}
```

- List values are comma-separated: `states: loading,error`
- A key with no value clears a list
- `add surface.Help` derives the id `surface.help`
- References are resolved automatically, so `modify flow.AddTodo actor: user` works

On success it prints the applied ops, the semantic diff, and `COMMITTED`. On failure
it prints the reason and exits 1 having changed nothing.

### `xir diff <old> <new>`

Semantic diff. A rename is `RENAMED`, not `REMOVED` + `ADDED`. Field changes print
before/after.

```bash
xir diff old.xir new.xir
# CHANGED capability.archiveProject (capability.archiveProject)
#     requires:
#         [permission.project.read]
#         -> [permission.project.manage]
```

## Generating

### `xir compile <f> --target <t> [--out <path>]`

| Target | Emits |
|---|---|
| `react` | components, state machines with hooks, interaction handlers, capability calls |
| `html` | sections per surface with `data-xir` ids |
| `a2ui` | agent-facing card descriptions |
| `docs` | markdown per node |
| `a11y` | roles, focus, live-region annotations |
| `playwright` | tests that walk the semantic chain |
| `xir` | canonical XIR (for normalisation) |

```bash
xir compile app.xir --target react --out src/App.jsx
xir compile app.xir --target playwright --out tests/app.spec.ts
```

The generated Playwright is behaviour, not markup:

```js
test('archiveProject', async ({ page }) => {
  await page.goto('/projectdetail');
  await page.getByTestId('component.projectDetail.archiveButton').click();
  await expect(page.getByRole('dialog')).toBeVisible();      // confirmation
  await page.getByRole('button', { name: /confirm/i }).click();
  await expect(page.getByTestId('field.project.status')).toHaveText(/archived/i);
});
```

## Verifying

### `xir test <f>`

Validate, build every projection, and confirm round-trip stability. Exit code 0 only
if all three pass.

```bash
xir test app.xir
# validate: clean
# react: 174 lines
# playwright: 41 lines
# round-trip: stable
```

### `xir bench`

Runs the semantic benchmark suite. Measures the model, **not** agent performance.

## Legacy

`ixl` is a pre-rename alias of `xir` and behaves identically.
