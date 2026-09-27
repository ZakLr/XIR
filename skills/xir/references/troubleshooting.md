# Troubleshooting

## `ERROR: invalid XIR at line N, column M`

Strict parse failed. The line and column are exact.

**Read the line.** Common causes:

| Message fragment | Cause |
|---|---|
| `No terminal matches ':'` | a colon where the grammar does not allow one, usually `output: X` written without the field keyword matching |
| `No terminal matches '.'` | a dotted reference in a field that takes a bare name |
| `No terminal matches 'P'` | a **single-character** name — check the token rule |
| `Unexpected token` near a keyword | a legacy keyword used with new syntax, or vice versa |

If you need the model anyway:

```bash
xir recover app.xir
```

It drops what will not parse and **reports every unresolved reference and every
inference**. Treat the result as provisional. Re-validate before patching.

## `PATCH REJECTED (rolled back): ...`

Good news: nothing changed. The reason is in the message.

| Message | What to do |
|---|---|
| `still referenced by ...` | update the named dependents, or use `strict=False` deliberately |
| `unknown reference: 'X'` | the id/name does not exist. `xir parse --level N` to list what does |
| `already exists: X` | choose another id, or rename the existing one |
| `patch rejected: <validation code>` | your change is internally inconsistent — fix the model, not the validator |

The transaction runs on a copy, so a rejected patch leaves the file untouched.

## `UNRESOLVED_REFERENCE: capability.X has an unresolved <rel> reference 'Y'`

A reference names something that does not exist. Either declare `Y`, or fix the name.

**Common gotcha:** state names are machine-scoped. If `error` is only in another
machine, it will not resolve from here.

**Second gotcha:** mutation targets are field ids. `mutates { Project.status }`
resolves; `mutates { status }` does not, unless a field is literally named that.

## `ORPHAN_COMPONENT: component X is not placed on any surface`

A component is declared but no `surface` lists it. Add it to the surface's
`components { }`, or accept it if it is genuinely standalone (in which case it will
keep reporting — the validator treats it as advisory for patches but still prints it).

## `UNREACHABLE_STATE` on a state you just added

No transition leads to it from the machine's initial state. Either add the
transition, or check that `initial:` names the state you think it does.

## `MISSING_INITIAL_STATE` but the machine has one

Normalization infers `initial` from the first state when you omit it, and reports the
omission. Declare it:

```bash
xir patch app.xir "patch { modify machine.projectList initial: state.projectList.loading }"
```

## The query answered about the wrong node

Names can be ambiguous. Resolution prefers the shallowest id, which is usually right
but not always. Use the **full id**:

```bash
xir trace app.xir capability.archiveProject     # not: archiveProject
```

Or scope by kind when a goal and a capability share a name:
`xir query app.xir "who can capability.createProject"`.

## `no <relation> edges from <id>`

A real negative: that edge does not exist. Check you are following the right relation
name. Valid relations are listed in `references/ontology.md`.

If you expected it, the model is missing the relationship — which is a finding worth
acting on, not a tool problem.

## Round-trip is unstable

```bash
xir test app.xir
```

reports `round-trip: UNSTABLE` when `parse → serialize → parse` is not equivalent.
This is a bug in the serializer or normalizer, not in your model. Report it with the
model and the diff.

## The model validates but the app is still wrong

The model is a claim, not the implementation. It can be internally consistent and
still not match reality. That is why provenance exists: check
`confidence` and `evidence` on anything load-bearing, and treat `inference` as a
hypothesis.
