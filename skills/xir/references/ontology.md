# Ontology reference

Every primitive, its id prefix, and what it is *for*. Read this when you need to
know which concept to reach for, or what a given id prefix means.

## Identity

Two separate things, and conflating them is the most common error:

- **id** — semantic identity, e.g. `capability.archiveProject`. Survives renames.
  Address nodes by this.
- **name** — display label, e.g. `archiveProject`. May be ambiguous. For display only.

```
rename capability.archiveProject to_name: archive
  -> id unchanged, name changed, every reference still valid
```

## Primitives

| Concept | Id prefix | Purpose | Typical use |
|---|---|---|---|
| **Experience** | `exp.` | the product root | one per model |
| **Goal** | `goal.` | an outcome a user is trying to achieve | link to the flow that achieves it |
| **Actor** | `actor.` | a role that may act | `manager`, `member`, `system` |
| **Permission** | `permission.` | a named authorisation | `project.archive` |
| **Entity** | `entity.` | a domain type | `Project` |
| **Field** | `field.` | an entity attribute | target of a mutation |
| **Event** | `event.` | something that happened | `ProjectArchived` |
| **Capability** | `capability.` | an invocable effect | the core of the product |
| **Surface** | `surface.` | a place that presents entities | `Dashboard` |
| **Component** | `component.` | a semantic UI unit | `ArchiveButton` |
| **Interaction** | `interaction.` | trigger → target → capability | the UI↔capability bridge |
| **Machine** | `machine.` | owns states and transitions | `projectList` |
| **State** | `state.` | a node in a machine | `loading` |
| **Transition** | `transition.` | source + event → target | `on dataReceived -> populated` |
| **Flow** | `flow.` | a user goal as a path | `CreateProject` |
| **Step** | `step.` | from → action → to inside a flow | |
| **Branch** | `branch.` | guarded outcomes | `success -> entity.project` |
| **Invariant** | `invariant.` | a rule scoped to a node | |
| **Meta** | `meta.` | requirement / observation / decision / assumption / inference / proposal | |

## Capability is the centre

Everything else exists to describe a capability.

```xir
capability archiveProject {
  input  { project: Project }   # what it takes
  output: Project               # what it returns
  requires: project.archive     # permission needed
  consumes: Project             # entity read
  produces: Project             # entity returned
  mutates { Project.status }    # entity field changed
  emits: ProjectArchived        # event announced
  confirmation: required        # destructive guard
  audit: required               # must be logged
}
```

Each field is a typed edge, not prose. That is the whole point:
`mutates { Project.status }` is machine-readable; the string `"archives the project"`
is not.

## Relationships (the edges you can traverse)

| Relation | From → To |
|---|---|
| `has` | experience → anything declared at top level |
| `grants` | actor → permission |
| `requires` | capability → permission |
| `consumes` / `produces` | capability → entity |
| `mutates` | capability → field |
| `emits` | capability → event |
| `causes` | capability → transition |
| `triggers` | event → transition |
| `invokes` | component / interaction / step → capability |
| `has-interaction` | component → interaction |
| `contains` | surface → component, machine → state, flow → step |
| `presents` | surface / component → entity |
| `has-state` | surface / component → machine |
| `transitions-to` | state → transition |
| `starts-at` | flow → surface |
| `leads-to` | step / branch → surface \| state \| entity |
| `achieved-by` / `achieves` | goal ↔ flow |
| `stepped-as` | actor → flow |
| `governed-by` | invariant → node |
| `evidenced-by` | meta → invariant \| evidence |

## Provenance and evidence

Every node can carry provenance; `meta` statements carry it explicitly.

```xir
inference archiveLocation {
  claim: "Archive belongs in the project overflow menu."
  confidence: probable
  evidence { screenshot.dashboard analytics.archiveUsage design.decision.D14 }
}
```

Confidence values: `confirmed`, `probable`, `inferred`, `tentative`, `proposed`,
`deprecated`, `unknown`.

**Hard rule:** an `inference` may never claim `confidence: confirmed`. The validator
rejects it. This is what stops a guess becoming a requirement.

## Resolution rules

A written reference may be:

| You write | It resolves to |
|---|---|
| `capability.project.archive` | that exact id |
| `archiveProject` | the node with that name |
| `Project.status` | `field.project.status` (path form) |
| `flow.AddTodo` | `flow.addTodo` (kind + name) |

Tie-breaking: exact match → case-insensitive → id-suffix → path-suffix, and among
candidates the **shallowest id wins**.

**State names are machine-scoped.** `error` in two machines is not ambiguous, because
resolution stays inside the declaring machine.

## Legacy forms

Still parse, and are upgraded on load:

| Legacy | Becomes |
|---|---|
| `actors { a b }` | `actor` declarations |
| `components { A B }` | `component` nodes (marked legacy) |
| `states: a b c` | a `machine` with states and **no transitions** |
| `A -> B` in a flow | an explicit `step` with from/to |
| `effects: x.y = z` | `mutates: [field.x.y]` |
| `step: Surface` | a step with only a target |

Legacy forms still resolve what they can; a bare edge's unresolved endpoints are not
reported as broken, because they are positional hints rather than typed references.
