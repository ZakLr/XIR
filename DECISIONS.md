# Decisions

## v0.3 — the semantic model is the product

1. **Separate the syntax AST from the semantic IR.** The parser reports what was
   written; `semantic/normalize.py` decides what it means. Graph, validation, query,
   patch, diff and compile read only the IR. Enforced by a test that greps for AST
   imports in the graph module.
2. **IDs are identity, names are display.** A rename keeps its id and is reported as
   `RENAMED`, not remove+add. Changing an id is an explicit, atomic operation.
3. **References are ids, never prose.** `mutates: [field.project.status]` replaces
   `effects: "project.status = archived"`. Legacy free text is upgraded on parse.
4. **Earley, not LALR.** The grammar has legitimate ambiguity between legacy and modern
   forms; LALR dropped alternatives and rejected valid input. Correctness first (§22 of
   the brief explicitly defers parser performance).
5. **One named rule per grammar alternative.** Lark filters anonymous tokens from rule
   callbacks, so a multi-alternative rule cannot report which branch matched.
6. **Unresolved references are preserved, not dropped.** They live in `Model.unresolved`
   so the validator can report them while the graph stays free of phantom nodes.
7. **Scope state names to their machine.** `error` in two machines is not ambiguous.
8. **Strict parsing is the default.** Invalid XIR raises with a line and column.
   `xir recover` is the explicit best-effort mode and always reports what it dropped.
9. **Reachability is only checked when transitions exist.** A bare `states: a b c` is a
   legacy form with nothing to traverse.
10. **Patches are transactions.** Validate, then commit or roll back. Removal refuses
    while references exist.
11. **React is the one serious target.** Other projections stay shallow on purpose.
12. **Benchmark results are labelled MEASURED / SIMULATED / INFERRED.** Simulated
    retrieval counts are never presented as agent performance.

## v0.2
- Python + Lark + Pydantic + NetworkX + Click
- Tolerant parser, identity derived from names
