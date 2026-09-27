# Changelog

## Unreleased
- **MCP server.** `xir-mcp <model>` exposes nine tools (`xir_summary`, `xir_validate`,
  `xir_trace`, `xir_inspect`, `xir_query`, `xir_follow`, `xir_diff`, `xir_compile`,
  `xir_health`) over stdio, so an agent traverses a model instead of grepping it. The
  tools route to the same library as the CLI, so both give the same answer.
  `xir-mcp --list-tools` prints the schema and needs no extra packages.
- **Distribution renamed to `xir-core`.** `xir` on PyPI belongs to an unrelated
  project. The command (`xir`), the import (`xir`) and the extension (`.xir`) are
  unchanged; only the PyPI name is new.
- **One emitter registry.** `xir.compiler.emit.TARGETS` is now the single source of
  truth for compile targets, shared by the CLI and the MCP server. It surfaced
  `to_tests`, a real emitter that was previously unreachable, now exposed as
  `--target tests`.
- **Documentation site.** `mkdocs.yml` plus `branding/build_site.py`, which stages the
  markdown that already lives in the repo and builds it in strict mode, so a broken
  relative link fails CI. Deploys to GitHub Pages from the verified artifact.
- **Brand assets, generated not hand-drawn.** `branding/generate_assets.py` produces the
  logo, wordmark, favicon and social card; `generate_diagram.py` renders the pipeline
  and the real semantic graph; `generate_demo.py` records a real terminal session.
- **Docs:** roadmap, community guide and star-history page, with an explicit statement
  that stars are not a benchmark and that no blinded agent trial has been run.
- CI gains docs and PyPI jobs. Publishing is tag-driven and uses trusted publishing,
  with a check that the tag matches the version in `pyproject.toml`.
- 119 tests, up from 80. Semantic round-trip still stable across all examples.

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
