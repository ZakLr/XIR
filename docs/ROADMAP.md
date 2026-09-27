# Roadmap

Direction, not a contract. Dated items are what the maintainers intend next.

## v0.3 — shipped

The semantic model and the things that make it trustworthy.

- [x] **Identity** — `derived_from` so a rename is a rename, not a remove plus an add
- [x] **Validation** — unresolved references, unreachable states, missing confirmation
      before destructive actions, unauthorised capabilities, unsupported confidence
- [x] **Queries by traversal** — `who can`, `affected`, `what happens when`, `show`
- [x] **Patches** — parse, simulate the effect, then apply; a patch you can preview
- [x] **Diff** — semantic, so a rename reads as a rename
- [x] **Semantic graph** — one graph, sixteen typed edge relations
- [x] **Provenance** — where each claim came from and how much it is trusted
- [x] **Context levels 0–6** — a precise slice instead of a pile of files
- [x] **Round-trip stability** — generated models validate and diff clean
- [x] **Compilers** — react, html, a2ui, docs, a11y, playwright, tests
- [x] **Model health** — validity separated from how well the model is specified
- [x] **MCP server** — nine tools, so an agent traverses instead of grepping
- [x] **Agent skill** — `skills/xir`, installable, works in any MCP-capable client

## v0.4 — next

Closing the gap between "the model is coherent" and "the model is right".

- [ ] **Blinded agent trial** — same task, same model, with and without XIR in context.
      Until this exists, every performance claim in this repo is `SIMULATED` or
      `INFERRED`, and the README says so.
- [ ] **Reconstruction experiment** — generate a product from a model, then compare
      against the original. A real number, not a demo GIF.
- [ ] **Inverse compiler** — recover a `.xir` model from a running app, so adoption
      does not require modelling everything by hand first.
- [ ] **Visual editor** — a model is a graph; people should be able to look at it.
- [ ] **Figma and screenshot import** — provenance-tagged, never silently trusted.
- [ ] **Schema registry** — shared entity and capability definitions, so two products
      in the same org speak about `project.status` the same way.

## Later

- [ ] **A2UI round-trip** — read a rendered A2UI tree back into the model
- [ ] **Accessibility as a first-class projection** — audit from the model, not the DOM
- [ ] **Version migration** — carry provenance through a model upgrade
- [ ] **VS Code extension** — hover a `.xir` ref and see the semantic chain

## Deliberately not planned

- **A hosted SaaS.** The model is a text file. Keeping it one is the point.
- **A proprietary schema.** XIR is a spec; anyone should be able to emit it.
- **A general-purpose workflow orchestrator.** XIR describes a product. It does not
  schedule work.

## Contributing to the roadmap

Open a discussion before you write the code. If a capability cannot be expressed in
the current ontology, that is an ontology problem, and the ontology is the thing worth
improving. See [DECISIONS.md](../DECISIONS.md) for why each line is drawn where it is, and
[OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md) for what is still undecided.

## Versioning

`0.x` means the language may still change shape. `xir validate` and
`xir diff` are the compatibility tools: if a model validates and round-trips clean, the
version it was written against did not lie to you. See [spec/versioning.md](../spec/versioning.md).
