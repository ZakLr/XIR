# Authoring

How to write a model that is worth having. Most of this is about honesty and
compactness.

## Order of declaration

Declare in dependency order. It is not enforced by the parser, but it makes the file
readable and mirrors how normalization runs:

```text
intent (goal, requirement/decision/inference)
  -> permission
    -> actor
      -> goal
        -> entity + field
          -> event
            -> capability
              -> machine (states + transitions)
                -> component
                  -> interaction
                    -> surface
                      -> flow (steps + branches)
                        -> invariant
```

A capability can only `requires` a permission that already exists, and can only
`mutates` a field that already exists.

## State the relationship, do not describe it

The single highest-value habit.

```xir
  # weak — an agent must infer the consequence
  capability archiveProject { effects: "archives the project" }

  # strong — the consequence is an edge
  capability archiveProject { mutates { Project.status }  emits: ProjectArchived }
```

Same for the UI bridge. A component that merely *looks* like it invokes a capability
is not connected to it:

```xir
  interaction archiveProject { trigger: click  target: component.projectDetail.archiveButton  invokes: capability.archiveProject }
```

Now the chain exists and can be traversed.

## Write state machines, not state lists

```xir
  # weak
  surface ProjectList { states: loading empty populated error }

  # strong
  state projectList {
    initial: loading
    loading  { on dataReceived -> populated  on emptyReceived -> empty  on failure -> error }
    empty    { on createProject -> loading }
    populated { on refresh -> refreshing  on ProjectArchived -> refreshing }
    refreshing { on success -> populated  on failure -> error }
    error    { on retry -> loading }
  }
  surface ProjectList { machine: projectList }
```

The list says which words exist. The machine says what can happen. Reachability,
dead ends and missing transitions are only checkable with the second.

Declare `initial:` explicitly. If you omit it, normalization infers one but the
validator still reports `MISSING_INITIAL_STATE` — the omission is real.

## Name states so the graph reads well

Prefer names that are meaningful in the machine, not globally unique ones. `error` in
three machines is fine and idiomatic; state names are machine-scoped, so do not
invent `errorState2`.

## Permissions before capabilities

If you write `capability deleteProject { requires: ... }` with no `permission`
declaration, validation reports `UNRESOLVED_REFERENCE`. Declare permissions first.

Give permissions dotted names — `order.cancel`, not `cancelOrderPermission`. Dots are
preserved in ids, so `permission order.cancel` becomes `permission.order.cancel`.

## Provenance: separate what you know from what you assume

| You are | Write |
|---|---|
| bound by a spec | `requirement:` |
| bound by a decision record | `decision:` |
| certain from reading code | `observation:` + `provenance { source: code }` |
| unsure | `inference:` + `confidence:` + `evidence { }` |

An `inference` may not claim `confidence: confirmed`; the validator rejects it. That
constraint is the point — it stops a guess hardening into a requirement without
someone noticing.

Attach evidence when you have it. `evidence { analytics.archiveUsage }` tells the
next agent (human or model) where the claim came from, which is the difference
between a re-derivable fact and an untraceable one.

## Compactness

XIR optimises semantic information per token. In practice:

- **Do not restate the ontology.** A `surface` does not need `interactive: true`; that
  is implied. Write the thing that is not implied.
- **Do not write layout in pixels.** `machine: projectList` says what is true. A
  breakpoint is not a semantic fact.
- **Reuse entities.** If two capabilities change the same thing, it is one `field`.
- **Do not duplicate what an edge already says.** If `interaction` `invokes`
  `capability`, the component does not need a comment repeating it.
- **Comment the non-obvious, not the obvious.** `provenance` and `evidence` carry
  what a reader cannot derive.

## Ids: let them be derived, pin only when needed

Ids are derived from names by default (`archiveProject` → `capability.archiveProject`).
Pin one explicitly when the derivation would be wrong or unstable:

```xir
  component ArchiveButton {
    id: component.projectDetail.archiveButton   # scoped by the surface, not global
    invokes: archiveProject
  }
```

## Invariants

An invariant is a rule scoped to a node. Use one when a rule spans more than a single
capability's fields:

```xir
  invariant archivedProjectsAreImmutable {
    rule: "archived projects cannot receive tasks"
    scope: entity.project
  }
```

The validator checks that the scope resolves. An invariant pointing at nothing is
worse than no invariant.

## Review checklist

Before committing a model:

```bash
xir validate app.xir      # zero findings
xir test app.xir          # projections build, round-trip stable
```

Then ask yourself:

- [ ] Does every capability that changes state declare `mutates`?
- [ ] Does every destructive capability declare `confirmation`?
- [ ] Is every permission actually held by an actor?
- [ ] Does every state machine declare `initial:`?
- [ ] Is anything I *assumed* written as an `inference` rather than a `requirement`?
- [ ] Would a new engineer answer "what happens when I click X" correctly from this
      model alone, without reading the implementation?
