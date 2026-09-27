# Semantics (v0.3)

`grammar.md` defines syntax. `ontology.md` defines concepts. This file defines meaning.
`semantic-graph.md` defines the graph.

## Pipeline

```text
source text
  -> strict Lark parse          (raises; never degrades)
  -> syntax AST                 (ast/nodes.py — literally what was written)
  -> normalization              (semantic/normalize.py — owns identity + resolution)
  -> semantic IR                (ir/model.py — the source of truth)
  -> typed graph                (semantic/graph.py)
  -> validation / query / patch / diff / compile
```

Nothing downstream of the IR may import the syntax AST.

## Identity

An id is semantic identity; a name is display. `ids.py` builds canonical ids
(`camel`-cased segments) and validates them. Dots in a written name are significant and
preserved, so `permission project.archive` yields `permission.project.archive`.

Renaming keeps the id:

```text
rename capability.archiveProject to_name: archive
  -> same id capability.archiveProject, new name
```

Changing the id is an identity change and is reported as add+remove in the diff.

## Resolution

A written reference may be an id (`capability.project.archive`), a name
(`archiveProject`), a path (`Project.status` → `field.project.status`), or a list.
Resolution is exact-match → case-insensitive → id-suffix → path-suffix, and ambiguity
is broken by preferring the shallowest id. When several nodes share a name
(`error` in two machines), the *declaring scope* wins: state names are machine-scoped.

Unresolvable references are recorded in `Model.unresolved` and reported by the
validator as `UNRESOLVED_REFERENCE`. Legacy loose forms (a bare `A -> B` flow edge)
resolve best-effort and do not report.

## Equivalence

Two models are equivalent when `diff()` prints `no semantic changes`. The canonical
serializer (`compiler/dsl.py`) emits the modern form, and
`parse(serialize(model))` must yield an equivalent model. Round-trip stability is
tested for every example.
