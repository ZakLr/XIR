# Contributing

Thanks for helping make the semantic model better.

1. Update the spec first (`spec/`, `research/`), then the code.
2. Keep the ontology minimal. Every primitive must justify itself against the
   design principles in `research/design-principles.md`.
3. Add a test with every behaviour change, and regenerate the goldens if you touch
   a compiler: `xir compile <example> --target <t> --out examples/<name>/expected.<t>`.
4. Before opening a PR: `pytest -q` and `python benchmarks/tasks.py`.
5. Record decisions in `DECISIONS.md` and open questions in `OPEN_QUESTIONS.md`.

Never commit anything under `.private/` — it is git-ignored by design.

