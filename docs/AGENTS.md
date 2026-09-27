# Agent guide

**You are working with XIR. Read this before you touch anything.**

XIR is a semantic intermediate representation for interactive products. When you have
an XIR model, you do **not** need to read React, Figma, screenshots or prose to
understand the product. The model already knows what the product *means*.

This guide tells you how to exploit that.

---

## 1. The one idea that matters

Source code, screenshots and prose describe an app. XIR describes what the app
**means and how it behaves**, with explicit relationships between things.

So a question like *"what happens when the user clicks Archive?"* is not a search
problem. It is a **traversal**:

```text
Component  ->  Interaction  ->  Capability  ->  Permission
                                        ->  Entity field (mutation)
                                        ->  Event
                                        ->  StateTransition
```

If you find yourself grepping strings to answer a behavioural question, you have used
the model wrong. Traverse instead.

---

## 2. Command surface

| Command | Use it for |
|---|---|
| `xir parse <f> --level N` | project the model at detail level N (0–6) |
| `xir validate <f>` | find every semantic inconsistency |
| `xir inspect <f> <ref>` | compact slice of one node and its relations |
| `xir trace <f> <capability>` | full behavioural chain for a capability |
| `xir query <f> "<phrase>"` | routed query: who-can, affected, lists |
| `xir follow <f> <id> <relation>` | structural traversal, `--depth N` |
| `xir diff <old> <new>` | semantic diff; renames ≠ remove+add |
| `xir patch <f> "<patch>"` | atomic, validated mutation |
| `xir compile <f> --target <t>` | react, html, a2ui, docs, a11y, playwright, xir |
| `xir recover <f>` | best-effort parse; **always reports what it dropped** |
| `xir test <f>` | validate + confirm projections and round-trip |
| `xir bench` | run the semantic benchmark suite |

`<ref>` accepts an id (`capability.archiveProject`), a name (`archiveProject`), or a
kind-qualified name (`capability.archiveProject`).

### Context levels

Never load the whole model. Pick the level that matches your question:

| Level | Contains |
|---|---|
| L0 | one-line product summary |
| L1 | entities, fields, actors, permissions, goals |
| L2 | capabilities and flows |
| L3 | surfaces |
| L4 | components and interactions |
| L5 | state machines, states, transitions |
| L6 | metadata, invariants, available projections |

---

## 3. Core recipes

### Understand a feature

```bash
xir trace app.xir archiveProject
```

Gives you: inputs, required permission, what it consumes/produces, what it mutates,
what it emits, whether confirmation/audit apply, which components expose it, which
flows use it, and which states it affects. That is the whole feature.

### Find where something is implemented in the UI

```bash
xir inspect examples/project-manager/app.xir surface.dashboard
xir query examples/project-manager/app.xir "affected field.project.status"
xir follow examples/project-manager/app.xir component.projectDetail.archiveButton invokes
```

Note the surface: the component lives on `surface.projectDetail` while the capability
belongs to the dashboard flow. **That mismatch is exactly the kind of thing string
search hides and the model shows.**

### Check authorisation

```bash
xir query app.xir "who can archiveProject"
# project.archive: manager
```

`member` is absent — the model knows who may and may not act, without reading an
`if`.

### Assess blast radius before changing something

```bash
xir query app.xir "affected field.project.status"
xir validate app.xir
```

### Review a change before accepting it

```bash
xir diff examples/todo/app.xir examples/todo/expected.xir
```

A rename shows as `RENAMED` with the id preserved. A remove+add shows as
`REMOVED`/`ADDED`. That distinction is the point: renaming a capability must not look
like deleting one and inventing another.

### Generate artifacts

```bash
xir compile examples/project-manager/app.xir --target react
xir compile examples/project-manager/app.xir --target playwright
```

The React target emits real components, state machines, interaction handlers and
capability calls. The Playwright target generates tests that walk
`interaction → capability → permission → mutation → event → state`, so the generated
test asserts behaviour rather than markup.

### Verify a model is healthy

```bash
xir validate examples/project-manager/app.xir
xir test examples/project-manager/app.xir
```

`xir test` also confirms the projections build and that round-trip is stable.

---

## 4. Modifying a model

**Always use `xir patch`. Never hand-edit and hope.**

Patches are transactions: resolve → apply → validate → **commit or roll back**. A patch
that would leave the model inconsistent is rejected with the reason, and nothing
changes.

```bash
xir patch examples/project-manager/app.xir "patch { rename capability.archiveProject to_name: archive }"
```

That keeps the id, so every reference stays valid. Multi-line patches read better when
they grow:

```bash
xir patch app.xir "patch {
  rename capability.archiveProject to_name: archive
}"
``` Changing an id is an explicit,
atomic operation:

```bash
xir patch app.xir "patch {
  rename capability.archiveProject to_id: capability.project.archive
}"
```

`remove` refuses while anything still points at the target and tells you who:

```text
PATCH REJECTED (rolled back): cannot remove capability.archiveProject:
still referenced by interaction.archiveProject.invokes, ...
```

That refusal is information. Either update the dependents first or use
`strict=False` deliberately.

### Patch syntax

```text
patch {
  rename <ref> to_name: <name>          # same id, new name
  rename <ref> to_id: <id>              # identity change, references rewritten
  modify <ref> <field>: <value>         # set a field; resolves refs automatically
  modify <ref> <list_field>:            # clear a list
  add <kind>.<Name> <field>: <value>    # create a node
  remove <ref>                          # guarded deletion
  deprecate <ref>                       # mark deprecated, keep it
  move <ref> to: <index>                # reorder
}
```

List values are comma-separated: `states: loading,error`.

---

## 5. Conventions

1. **Reference nodes by id.** Ids are identity. Names are display labels and can be
   ambiguous (`error` exists in several machines; state names are machine-scoped).
2. **Do not re-derive relationships.** If the model says
   `capability.archiveProject mutates field.project.status`, believe it. Do not
   re-infer it from a name.
3. **Respect provenance.** Every node can carry `source`, `reference`, `confidence`
   and `evidence`. An `inference` may never claim `confidence: confirmed`. When you
   are reasoning from inferred material, say so — that is the point of the field.
4. **Validate after every change.** A patch that validates is a patch you can trust.
5. **Use `recover` deliberately.** `xir parse` is strict and will reject bad input.
   `xir recover` is best-effort and reports what it could not resolve. Never feed a
   recovered model into a patch without re-validating.
6. **Prefer `trace` over `inspect`** for capabilities, and `inspect` for everything
   else. `trace` is the behavioural slice; `inspect` is the structural one.

---

## 6. The ontology, briefly

| Concept | What it means |
|---|---|
| **Experience** | the product root |
| **Goal** | an outcome a user is trying to achieve |
| **Actor** | a role that may act; grants permissions |
| **Permission** | a named authorisation, e.g. `project.archive` |
| **Entity / Field** | domain types and their attributes; mutation targets |
| **Event** | something that happened; emitted by capabilities |
| **Capability** | an invocable effect — the heart of the model |
| **Surface** | a place that presents entities and contains components |
| **Component** | a semantic UI unit: presents, invokes, has states |
| **Interaction** | trigger → target → capability; the UI bridge |
| **Machine / State / Transition** | explicit behaviour, machine-traversable |
| **Flow / Step / Branch** | a user goal as a path with actions and outcomes |
| **Invariant** | a rule scoped to a node |
| **Provenance** | source, confidence, evidence |

Full definitions: [`spec/ontology.md`](../spec/ontology.md).

---

## 7. Worked example

```bash
$ xir trace examples/project-manager/app.xir archiveProject
CAPABILITY: archiveProject
  ID: capability.archiveProject
  INPUT: project: Project
  OUTPUT: Project  [entity.project]
  REQUIRES: project.archive  [permission.project.archive]
  CONSUMES: Project  [entity.project]
  MUTATES: status  [field.project.status]
  EMITS: ProjectArchived  [event.projectArchived]
  CONFIRMATION: required
  AUDIT: required
  EXPOSED BY: ArchiveButton  [component.projectDetail.archiveButton]
  EXPOSED BY: archiveProject  [interaction.archiveProject]
  FLOW: CreateProject  [flow.createProject]
  STATE: confirming  [state.projectDetailActions.confirming]
```

Every line is a typed edge, not a string match. The emitted `ProjectArchived` event
drives `transition.projectList.populated.projectArchived`, which is how the list
refreshes after an archive — a consequence stated in the model, not discovered by
reading code.

---

## 8. Writing new XIR

Full syntax: [`spec/grammar.md`](../spec/grammar.md). The shortest useful example:

```xir
experience Shop {
  goal: "Sell goods."
  actor buyer { permissions { order.place } }
  permission order.place { description: "Place an order." }
  entity Order { id: ID  status: draft | active }
  capability placeOrder {
    input { order: Order }
    output: Order
    requires: order.place
    mutates { Order.status }
    confirmation: required
  }
  interaction placeOrder { trigger: click  target: component.cart.submit  invokes: placeOrder }
  component Submit { id: component.cart.submit  invokes: placeOrder }
  surface Cart { presents: Order[]  components { Submit } }
  flow Checkout { actor: buyer  entry { surface: surface.cart }  step: submit }
}
```

Legacy flat forms still parse and are upgraded on load: `actors { a b }`,
`components { A B }`, `states: a b c`, `A -> B` flow edges, and
`effects: x.y = z` (which becomes a structured `mutates`).

---

## 9. Honest limits

- XIR tells you what the model *says*. If the model is wrong, your answer is wrong.
  Validate first.
- Legacy examples have few transitions, so reachability analysis has little to chew
  on. `examples/project-manager` is the fully-specified reference.
- Benchmarks measure the semantic model, **not agent performance**. No blinded agent
  trial has been run. Do not cite XIR token savings as a measured result.
- `xir recover` produces a best-effort model. It is not authoritative.

---

## Further reading

| Doc | For |
|---|---|
| [`spec/ontology.md`](../spec/ontology.md) | every primitive, precisely |
| [`spec/semantic-graph.md`](../spec/semantic-graph.md) | node kinds and every edge relation |
| [`spec/queries.md`](../spec/queries.md) | the query surface in detail |
| [`spec/patches.md`](../spec/patches.md) | patch ops and transaction semantics |
| [`spec/validation.md`](../spec/validation.md) | every finding code |
| [`spec/grammar.md`](../spec/grammar.md) | full syntax, legacy forms, strictness |
| [`docs/v0.3-audit.md`](v0.3-audit.md) | what the model does that code cannot |
