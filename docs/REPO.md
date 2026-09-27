# Repo guide

**You are reading this repo, not using the product.** Start here to understand the
layout, run everything, and see where to contribute.

For *using* XIR — as an agent or a developer — read
[`docs/AGENTS.md`](AGENTS.md) instead.

---

## 1. What this repository is

XIR is a semantic intermediate representation for interactive products. You describe a
product's intent, capabilities, surfaces, state machines and flows; the model compiles
to React, HTML, A2UI, docs, accessibility metadata and Playwright tests.

The claim being tested: an agent given a semantic model can understand, modify,
validate and compile a product with less ambiguity than one reading scattered source,
screenshots and prose.

**That claim is not yet proven end to end.** What is proven is that the model contains
the structure needed to answer behavioural questions by traversal, and that it is
compact and round-trip stable. See [`benchmarks/report.md`](../benchmarks/report.md)
for what is measured versus simulated.

---

## 2. Layout

```text
src/xir/
  ast/         syntax AST — what the parser literally found
  ir/          SEMANTIC IR + identity  ← the source of truth
  parser/      grammar.lark, strict parser, strict/recovery policy
  semantic/    normalization, typed graph, L0-L6 context levels
  query/       show / trace / follow / who-can / affected
  validator/   graph-based semantic checks
  patch/       atomic transactions
  diff/        semantic, rename-aware
  compiler/    emitters + canonical serializer
  cli/         the xir command

spec/          grammar, ontology, semantics, semantic-graph, queries,
               patches, validation, provenance, versioning
research/      landscape, related systems, competitors, differentiation,
               principles, open problems
docs/          this file, AGENTS.md, v0.3-audit.md, logo
examples/      five models, each with golden projections
benchmarks/    the suite and the results report
tests/         80 tests
```

### The one architectural rule

`src/xir/ir/` is the source of truth. Graph, validator, query, patch, diff and
compiler **must not import the syntax AST**. That separation is what makes identity,
resolution and validation consistent everywhere, and it is enforced by a test that
greps the graph module for AST imports.

The pipeline:

```text
source .xir
  -> strict parse          (invalid input raises; never degrades silently)
  -> syntax AST            (literally what was written)
  -> normalization         (owns identity + reference resolution)
  -> semantic IR           (the source of truth)
  -> typed graph
  -> validate / query / patch / diff / compile
```

---

## 3. Run it

```bash
git clone https://github.com/ZakLr/XIR.git
cd XIR
pip install -e .[dev]

pytest -q                    # 80 tests
python benchmarks/tasks.py   # semantic benchmark
xir validate examples/project-manager/app.xir
xir trace examples/project-manager/app.xir archiveProject
```

Requires Python ≥ 3.10. Dependencies: `lark`, `pydantic`, `networkx`, `click`.

The `ixl` command is kept as an alias of `xir` from before the rename.

---

## 4. Where to start reading the code

If you want to understand one thing well:

| Question | Read, in order |
|---|---|
| What can a model express? | `spec/ontology.md` → `examples/project-manager/app.xir` |
| How are relationships stored? | `src/xir/ir/model.py` → `src/xir/semantic/graph.py` |
| How does text become semantics? | `src/xir/semantic/normalize.py` |
| How are questions answered? | `src/xir/query/engine.py` |
| What is considered invalid? | `src/xir/validator/validate.py` |
| Why is it built this way? | `docs/v0.3-audit.md` → `DECISIONS.md` |

`examples/project-manager/app.xir` is the canonical reference model: it exercises
goals, permissions, actors, events, state machines, interactions, invariants and
evidence. Read it first.

---

## 5. The pipeline in practice

```bash
xir parse app.xir --level 2        # a capability/flow-level view
xir inspect app.xir surface.dashboard
xir follow app.xir capability.archiveProject emits
xir patch app.xir "patch { rename capability.archiveProject to_name: archive }"
xir diff old.xir new.xir
xir compile app.xir --target react --out src/App.jsx
```

Every command operates on the semantic IR. Full surface in
[`docs/AGENTS.md`](AGENTS.md) and [`spec/queries.md`](../spec/queries.md).

---

## 6. Contributing

1. Change `spec/` before you change code, so the docs cannot drift.
2. Add a test with every behaviour change.
3. If you touch a compiler, regenerate the goldens:
   ```bash
   xir compile examples/todo/app.xir --target react --out examples/todo/expected.react
   ```
4. Before opening a PR: `pytest -q` and `python benchmarks/tasks.py`.
5. Record architectural decisions in `DECISIONS.md`, uncertainties in
   `OPEN_QUESTIONS.md`.

New ontology primitives are held to a high bar. Before adding one, show what it
enables that the existing set cannot, and what it costs in context per token. See
`research/design-principles.md`.

### What CI checks

- tests across Python 3.10–3.13
- the benchmark suite runs
- **the built wheel is installed into a clean venv and used** — the parser loads its
  grammar from package data at runtime, so a wheel that omits it would install
  cleanly and then fail on first use. This check exists because that bug shipped once.

---

## 7. What is public

Everything tracked in git: `src/`, `tests/`, `spec/`, `research/`, `docs/`,
`examples/`, `benchmarks/`, community files, CI config.

`.private/` holds personal briefs and scratch notes. It is git-ignored and never
published. Delete it before publishing a fork. The mapping from private notes to
public docs is in `.private/README.md`.

---

## 8. Project status

Current: **v0.3**, alpha. Solid: the semantic model, identity, validation, queries,
atomic patches, round-trip stability, one real compiler target. Open: blinded agent
evaluation, formal temporal verification, extraction from existing codebases, a
versioned extension mechanism. Tracked in [`OPEN_QUESTIONS.md`](../OPEN_QUESTIONS.md).

Recent direction is recorded in [`CHANGELOG.md`](../CHANGELOG.md); the reasoning is in
[`DECISIONS.md`](../DECISIONS.md).

---

## 9. License

**AGPLv3+.** Free to use, modify and share. If you run a modified version as a network
service you must offer its source to your users (§13). See [`LICENSE`](../LICENSE).

This is a deliberate choice: a semantic layer is most valuable when improvements flow
back rather than being locked into a proprietary product. If that does not suit you,
do not use it commercially without discussing it upstream.
