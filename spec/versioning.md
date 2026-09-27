# Versioning

Semantic models evolve; version from day one (Sec 45).

- v1: `version: N` parsed (strict + tolerant), emitted, diffed (`Changed version: a -> b`).
  Canonical emitter normalizes formatting so textual drift doesn't break identity.
- Planned: `migration` blocks and `compatibility` checks; `diff old new` as migration source.
- Rule: additive changes minor; renames/removals/meaning changes major with migration notes.
