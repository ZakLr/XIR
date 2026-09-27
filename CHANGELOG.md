# Changelog

## 0.3.0
- Separated the syntax AST from the semantic IR; graph, validation, query, patch, diff
  and compile now read only the IR.
- Stable semantic identity: canonical ids, identity-preserving renames, rename-aware diff.
- New primitives: Goal, Permission, Event, Component, Interaction, state machines with
  explicit transitions, rich flow steps and branches, Invariant, structured evidence.
- Typed semantic graph with named relations and no phantom nodes.
- Query engine answers from graph traversal: show, trace, follow, who-can, affected.
- Atomic, validating patch transactions with reference-safe rename and guarded removal.
- Validation rebuilt on the graph: identity, capabilities, components, interactions,
  state machines, flows, security and evidence checks.
- Strict parsing by default with an explicit `xir recover` mode.
- Real React target and semantic Playwright generation.
- Honest benchmark: 40/40 measured, results labelled MEASURED / SIMULATED / INFERRED.
- 80 tests; semantic round-trip stable across all examples.
- Agent guide (docs/AGENTS.md) and repository guide (docs/REPO.md), with tests that
  execute every documented command and parse every documented XIR snippet.

## 1.0.0
- Initial public release of the XIR skeleton (previously IXL), AGPLv3+.
