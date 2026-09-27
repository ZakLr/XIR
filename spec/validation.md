# Validation (v0.3)

Engine: `src/xir/validator/validate.py`. Runs on the semantic IR. Every finding is a
`Finding(code, message, subject_id)` so callers get a stable code and the exact node.

## Identity
`DUPLICATE_ID`, `INVALID_ID`, `DANGLING_REFERENCE`, `UNRESOLVED_REFERENCE`

## Capabilities
`INVALID_CAPABILITY`, `INVALID_INPUT_TYPE`, `INVALID_OUTPUT_REF`, `INVALID_MUTATION`,
`INVALID_EVENT`, `MISSING_CONFIRMATION`

## Components
`EMPTY_COMPONENT`, `INVALID_CAPABILITY_REF`, `INVALID_CHILD_COMPONENT`, `ORPHAN_COMPONENT`

## Interactions
`INTERACTION_WITHOUT_CAPABILITY`, `INVALID_TARGET_COMPONENT`, `INVALID_CAPABILITY_REF`

## State machines
`EMPTY_MACHINE`, `MISSING_INITIAL_STATE`, `INVALID_INITIAL_STATE`,
`INVALID_TRANSITION_TARGET`, `UNREACHABLE_STATE`, `DEAD_END_STATE`

Reachability is only checked when the machine actually declares transitions: a bare
list of states is a legacy form with nothing to traverse.

## Flows
`DEAD_END_FLOW`, `INVALID_ACTOR`, `INVALID_GOAL`, `INVALID_SURFACE`, `INVALID_INTERACTION`,
`UNREACHABLE_STEP`, `BROKEN_BRANCH`

## Security
`UNAUTHORIZED_CAPABILITY`, `UNREACHABLE_CAPABILITY` — the
`actor -> interaction -> capability -> permission` chain must be satisfiable. A
capability whose permission nobody holds is reported as unreachable.

## Evidence
`INVALID_CONFIDENCE`, `UNSUPPORTED_CONFIDENCE`, `INVALID_PROVENANCE`, `EMPTY_CLAIM`

An `inference` may never claim `confidence: confirmed`.

## Advisory findings
`EMPTY_COMPONENT` and `ORPHAN_COMPONENT` are advisory: a patch that introduces only
those still commits.

## Usage

```text
$ xir validate app.xir
valid: ProjectManager [exp.projectManager] 80 semantic nodes
$ xir validate broken.xir
UNRESOLVED_REFERENCE: capability.x has an unresolved emits reference 'Ghost' [capability.x]
```
