# Ontology (v0.3)

Primitives live in `src/xir/ir/model.py`. Every one has a stable `id`, a display
`name`, and typed references. Identity is semantic; names are syntax-level.

| Kind | ID prefix | Purpose | Core? |
|---|---|---|---|
| Experience | `exp.` | product root, holds intent + version | yes |
| Goal | `goal.` | user/product outcome, linkable to flows and actors | yes |
| Actor | `actor.` | a role that may act; grants permissions | yes |
| Permission | `permission.` | a named authorization, e.g. `project.archive` | yes |
| Entity | `entity.` | domain type | yes |
| Field | `field.` | entity attribute; the target of a mutation | yes |
| Event | `event.` | something that happened; emitted by capabilities | yes |
| Capability | `capability.` | invocable effect: input/output/requires/consumes/produces/mutates/emits | yes |
| Surface | `surface.` | a screen/place that presents entities and contains components | yes |
| Component | `component.` | semantic UI unit: presents, invokes, has states, contains | yes |
| Interaction | `interaction.` | trigger → target → capability; the UI↔capability bridge | yes |
| Machine | `machine.` | owns states and transitions | yes |
| State | `state.` | a node in a machine | yes |
| Transition | `transition.` | source state + event → target state (+ guard, action) | yes |
| Flow | `flow.` | a user goal with entry, steps and branches | yes |
| Step | `step.` | from → action → to inside a flow | yes |
| Branch | `branch.` | guarded outcomes from a point in a flow | yes |
| Invariant | `invariant.` | a rule scoped to a node | extension |
| Meta | `meta.` | requirement/observation/decision/assumption/inference/proposal | extension |
| Provenance | (on every node) | source, reference, confidence, evidence | extension |

## Rules

- **Identity over name.** Renaming a node does not change its id. `ids.py` enforces the
  pattern; an invalid id is a hard error, never a silently new node.
- **References are ids.** A capability does not store `"project.status = archived"`; it
  stores `mutates=["field.project.status"]`. Legacy `effects:` text is upgraded during
  normalization.
- **State names are machine-scoped.** `error` in two machines is not ambiguous.
- **Defaults are marked.** A machine with no `initial:` gets one inferred, but
  `initial_declared` stays false so validation can report the omission.
- **Unresolved references are kept.** They land in `Model.unresolved` rather than being
  dropped, so the validator can report them; the graph stays free of phantom nodes.
