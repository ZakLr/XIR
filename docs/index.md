---
hide:
  - navigation
  - toc
---

# XIR

**The semantic IR for interactive products.**

Give an agent the exact semantic slice it needs to understand, modify, validate, test
and compile part of a product.

<div class="grid cards" markdown>

- :material-rocket-launch: **I want to use it**

    The [agent guide](AGENTS.md) covers the command surface, traversal recipes, the
    patch workflow and the conventions that keep answers trustworthy.

    [:octicons-arrow-right-24: Agent guide](AGENTS.md)

- :material-bookend-variant: **I want to understand the language**

    Start with the [ontology](../spec/ontology.md), then the
    [semantic graph](../spec/semantic-graph.md) everything is built on.

    [:octicons-arrow-right-24: Ontology](../spec/ontology.md)

- :material-source-branch: **I want to work on it**

    The [repository guide](REPO.md) covers layout, how to run the tests, and where to
    start reading.

    [:octicons-arrow-right-24: Repository guide](REPO.md)

- :material-puzzle: **I want to see it work**

    The [benchmark report](../benchmarks/report.md) says exactly what is measured and
    what is not.

    [:octicons-arrow-right-24: Benchmarks](../benchmarks/report.md)

</div>

## The problem

An interactive product lives as disconnected artifacts: **code, screenshots, Figma,
prose, schemas**. An agent reading all of that burns tokens, guesses at intent, and
cannot tell a *relationship* from a *coincidence of words*.

## The idea

A behavioural question is a **traversal**, not a search.

```text
Component -> Interaction -> Capability -> Permission
                               |-> Entity field (mutation)
                               |-> Event -> StateTransition
                               \-> Flow -> Outcome
```

## Install

```bash
pip install xir-core
```

The command is `xir`, the import is `xir`, the extension is `.xir`. The distribution is
`xir-core` because `xir` on PyPI belongs to an unrelated project.

## First commands

```bash
xir validate app.xir                     # is the model coherent?
xir trace    app.xir archiveProject      # what does this feature do?
xir query    app.xir "who can archiveProject"
xir compile  app.xir --target react
```

## If your agent speaks MCP

```bash
pip install 'xir-core[mcp]'
xir-mcp path/to/app.xir
```

Nine tools, so the model is traversed rather than grepped. `xir-mcp --list-tools` prints
the schema.

## What is measured, and what is not

The semantic model, its identity model, validation, query, patches and round-trip
stability are implemented and tested. **Whether XIR makes an LLM agent faster or more
correct has not been proven** — no blinded agent trial has been run. Benchmark results
are labelled `MEASURED` / `SIMULATED` / `INFERRED`; see the
[benchmark report](../benchmarks/report.md).

---

<div class="xir-footer" markdown>

**AGPLv3+** · [GitHub](https://github.com/ZakLr/XIR) ·
[Discussions](https://github.com/ZakLr/XIR/discussions) ·
[PyPI](https://pypi.org/project/xir-core/)

</div>
