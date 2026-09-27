# Open questions

## Resolved in v0.3
- Provenance/evidence with structured sources and confidence
- Version stanza
- Full patch set (add/remove/replace/modify/move/rename/deprecate) as an atomic transaction
- L0–L6 context slicing
- Real React target and semantic Playwright generation
- Five examples, including a domain extension (clinic)

## Open
- **Blinded agent evaluation.** The benchmark measures the semantic model, not agent
  performance. A study giving agents equivalent tasks with XIR vs prose/JSON/source is
  the missing proof. Everything in `benchmarks/report.md` is labelled accordingly.
- **Formal temporal verification.** The validator checks reachability, dead ends and
  reference integrity, not temporal logic over runs.
- **Extraction from existing code.** Reverse-engineering a React app into a model is
  out of scope for v0.3; authoring and querying are the focus.
- **Layout semantics beyond container/constraint basics.** No pixel or motion model.
- **Extension packaging.** Domain extensions (healthcare, gaming) are examples today,
  not a versioned extension mechanism.
- **Incremental parsing.** Deliberately deferred; the semantic model was the bottleneck.
