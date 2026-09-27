# Patches (v0.3)

Engine: `src/xir/patch/patch.py`. Patches are **transactions**:

```text
PATCH
  -> resolve semantic ids
  -> apply to a deep copy
  -> rebuild (graph is derived, so nothing to do)
  -> validate
  -> commit  OR  rollback
```

A patch never leaves the model partially invalid. If validation reports a blocking
finding, the change is discarded and `PatchError` is raised with the reasons.

## Operations

| Op | Effect |
|---|---|
| `rename` | new name, same id; all references keep pointing at it |
| `rename ... to_id:` | identity change; every reference is rewritten atomically |
| `modify` | sets fields; list fields resolve each element to an id; `key:` with no value clears a list |
| `add` | creates a node; `add surface.Help` derives `surface.help` |
| `remove` | refuses while any node still references the target (reports who) |
| `deprecate` | sets provenance confidence to `deprecated` |
| `move` | reorders within its bucket |

## Syntax

```text
patch {
  rename capability.archiveProject to_name: archive
  modify actor.member permissions:
  add surface.Help states: loading,error
  remove component.obsolete
}
```

## Removal safety

`remove` computes every inbound reference first. If any exist and the transaction is
strict, it refuses:

```text
PATCH REJECTED (rolled back): cannot remove capability.archiveProject:
still referenced by interaction.archiveProject.invokes, component...archiveButton.invokes
```

Pass `strict=False` to cascade the removal instead.

## Agent workflow

```text
query -> identify affected nodes -> check invariants -> propose patch
      -> validate -> apply -> compile -> test -> diff
```

`xir patch <file> "<patch>"` prints the applied ops, the semantic diff, and `COMMITTED`,
or the rejection reason and exits non-zero.
