# Validation

Implemented in `src/xir/validator/validate.py` (codes are message prefixes):

- `duplicate ID` — same kind+name twice.
- `undefined reference` — capability input/output type not entity nor Text/ID/Int/Bool/Float.
- `invalid capability` — no input and no output.
- `missing states` / `missing required states` — surface needs states incl. loading+error.
- `missing transitions` — single-state surface.
- `dead-end flow` — flow with no steps.
- `broken reference` — flow actor not in declared actors.
- `unreachable state` — flow step matching no surface/capability/entity/flow (first only).
- `circular dependency` — flow looping single step.
- `invalid permissions` — destructive capability (delete/destroy/archive/remove) w/o confirmation.
- `inconsistent domain` — surface presents unknown entity.
