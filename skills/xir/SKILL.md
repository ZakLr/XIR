---
name: xir
description: >
  Build, reason about, and change interactive software through a semantic model
  instead of through scattered code, screenshots and prose. XIR (eXperience IR) is a
  typed intermediate representation where intent, actors, permissions, domain
  entities, capabilities, events, surfaces, components, interactions, state machines
  and user flows are explicit, ID-addressable and traversable — so behavioural
  questions are answered by walking the model, not by grepping strings. Use it to
  conceive a product before coding it, to answer "what happens when the user does X",
  to check who is allowed to do what, to assess the blast radius of a change, to
  generate React/HTML/A2UI/docs/accessibility/Playwright from one source, or to
  reverse-engineer meaning from an existing product.
  Trigger: "xir", ".xir file", "semantic model", "product model", "model this app",
  "conceive this software", "what happens when the user clicks", "which actor can",
  "what breaks if I change", "user flow", "state machine for the UI", "screen states",
  "capability", "permission model", "generate React from a model", "agent-readable
  product spec", "interactive product IR".
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
license: AGPL-3.0-or-later
---

# XIR — conceive software semantically, then compile it

The premise: **an interactive product should have a semantic IR, the way a program has
an IR.** You author what the product *means* and how it *behaves*; the model projects
to UI code, tests, and docs.

Most agent failures on UI work are not coding failures. They are *comprehension*
failures: the agent cannot tell whether `archiveButton` is connected to
`archiveProject`, because that relationship exists only as a coincidence of names
across files. XIR makes it a typed edge.

## The one rule

**A behavioural question is a traversal, not a search.**

```text
Component → Interaction → Capability → Permission
                              ├──→ Entity field (mutation)
                              ├──→ Event → StateTransition
                              └──→ Flow → Outcome
```

If you find yourself grepping for a string to answer a behavioural question, you are
using the model wrong. Traverse instead.

## Setup

```bash
pip install xir            # or: pip install -e . from a checkout
xir --help
```

Requires Python ≥ 3.10. No runtime services, no network, no build step to *read* a
model. For everything below, `app.xir` is any XIR model file.

## Orient before you act

Never read a whole model. Pick the smallest slice that answers your question.

```bash
xir parse app.xir --level 0     # one line: what this product is
xir parse app.xir --level 2     # capabilities + flows
xir parse app.xir --level 5     # state machines + transitions
```

| Level | Contains |
|---|---|
| L0 | product summary |
| L1 | entities, fields, actors, permissions, goals |
| L2 | capabilities, flows |
| L3 | surfaces |
| L4 | components, interactions |
| L5 | state machines, states, transitions |
| L6 | metadata, invariants, available projections |

## Answer questions with the model

| The question | The command |
|---|---|
| What does this feature actually do? | `xir trace app.xir archiveProject` |
| What does this screen contain? | `xir inspect app.xir surface.dashboard` |
| Who is allowed to do this? | `xir query app.xir "who can archiveProject"` |
| What breaks if I change this? | `xir query app.xir "affected field.project.status"` |
| Where in the UI does this run? | `xir follow app.xir capability.archiveProject invokes` |
| What states exist, and how do they connect? | `xir inspect app.xir machine.projectList` |
| Is this model internally consistent? | `xir validate app.xir` |

`trace` is the behavioural slice (input, permission, mutation, event, exposure,
flows, states). `inspect` is the structural one. When unsure, `trace` the capability.

## Change a model safely

**Always patch. Never hand-edit and hope.**

```bash
xir patch app.xir "patch { rename capability.archiveProject to_name: archive }"
```

Patches are transactions: resolve → apply → validate → **commit or roll back**. A patch
that would leave the model inconsistent is rejected, with the reason, and nothing
changes.

```bash
xir patch app.xir "patch { remove capability.archiveProject }"
# PATCH REJECTED (rolled back): cannot remove capability.archiveProject:
# still referenced by interaction.archiveProject.invokes, ...
```

That rejection is information, not an obstacle. Update the dependents, or make the
removal explicit with `strict=False`.

Identity is preserved by a name change. Changing an id is an explicit, atomic
operation that rewrites every reference or rolls back:

```bash
xir patch app.xir "patch { rename capability.archiveProject to_id: capability.project.archive }"
```

Review before accepting:

```bash
xir diff old.xir new.xir     # RENAMED ≠ REMOVED + ADDED
```

## Conceiving a new product

Work semantics-first. The order matters — each step is cheaper than the next.

1. **Intent.** `goal: "..."`, and the `requirement:` / `decision:` statements you are
   actually sure of. Mark guesses as `inference` with a confidence. See
   `references/authoring.md`.
2. **Domain.** `entity` + `field`. This is what gets mutated.
3. **Authorization.** `permission`, and `actor` with `permissions { }`. Do this
   *before* capabilities, so capabilities can declare `requires`.
4. **Capabilities.** `input` / `output` / `requires` / `consumes` / `mutates` /
   `emits` / `confirmation` / `audit`. This is the core of the product.
5. **Events and behaviour.** `event`, then a `state` machine with explicit transitions.
6. **UI.** `interaction` (trigger → target → capability), `component`, then `surface`.
7. **Flows.** `flow` with `entry`, `step` (from → action → to) and `branch`.
8. **Validate, then compile.**

```bash
xir validate app.xir
xir compile app.xir --target react --out src/App.jsx
xir compile app.xir --target playwright --out tests/app.spec.ts
```

The React target emits real components, state machines, interaction handlers and
capability calls. The Playwright target generates tests that walk
`interaction → capability → permission → mutation → event → state`, so the generated
test asserts behaviour rather than markup.

## Reverse-engineering an existing product

Model what you can *prove*, and mark the rest as inference.

1. Inventory the screens and the actions a user can take → `surface`, `interaction`.
2. For each action, find what it changes → `capability` with `mutates`.
3. Note where the app can be in a broken or partial state → `state` machine.
4. Note who can do what → `permission` + `actor`.
5. Anything you inferred rather than observed becomes `inference` with
   `confidence: probable` and `evidence { ... }`.

That discipline is the point. An agent that cannot tell an observation from an
inference will confidently ship a guess as a requirement.

## Discipline

1. **Validate first.** `xir validate app.xir`. A model that does not validate will
   produce confidently wrong answers.
2. **Reference by id.** Ids are identity; names are labels and can be ambiguous
   (`error` exists in several state machines — state names are machine-scoped).
3. **Never re-derive a stated relationship.** If the model says
   `archiveProject mutates field.project.status`, that is the answer. Do not infer it
   from a name.
4. **Respect provenance.** An `inference` may never claim `confidence: confirmed`.
   When your answer rests on inferred material, say so.
5. **`xir parse` is strict.** Bad input raises with a line and column. `xir recover`
   is best-effort and reports everything it dropped — never patch a recovered model
   without re-validating.
6. **Claim only what you measured.** XIR's own benchmarks are labelled
   MEASURED / SIMULATED / INFERRED. No blinded agent trial has been run. Do not tell
   anyone XIR saves tokens for agents as a measured fact.

## Common mistakes

| Mistake | Instead |
|---|---|
| Grepping the source to find what a button does | `xir trace app.xir <capability>` |
| Reading the whole model into context | `xir parse --level N`, then one `inspect` |
| Hand-editing `.xir` and moving on | `xir patch` — it validates and rolls back |
| Deleting a capability, then fixing the fallout | read the rejection; it names every dependent |
| Renaming and rewriting references by hand | `rename` updates references atomically |
| Treating an inference as a requirement | check `confidence` and `evidence` |
| Assuming a component and capability with similar names are related | follow the actual edge |

## Reference material

| File | Read it when |
|---|---|
| `references/ontology.md` | you need the exact meaning of a primitive or id prefix |
| `references/cli.md` | you need the full command surface and output shapes |
| `references/patterns.md` | you want worked end-to-end recipes |
| `references/authoring.md` | you are writing a new model and want it to be good |
| `references/troubleshooting.md` | a command failed or a patch was rejected |
| `scripts/xir_health.py` | you want a one-shot report on a model's state |

## When not to use this

- **Pure algorithmic code** with no interactive surface — a semantic UI model is noise.
- **The user asked for a one-line change** to an existing file — just do it.
- **You have no XIR file and the task is not about conceiving a product** — do not
  introduce the tool uninvited. Building a model first is justified when the work
  touches behaviour, permissions, state or flows across more than a file or two.
