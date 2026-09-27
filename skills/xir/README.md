# XIR skill

An agent skill that teaches an AI agent to conceive, reason about and modify
interactive software through [XIR](https://github.com/ZakLr/XIR), a typed semantic
intermediate representation — instead of through scattered source code, screenshots
and prose.

## Install

Copy the `xir/` directory into your skills folder:

```bash
# opencode
cp -r skills/xir ~/.config/opencode/skills/

# Claude Code
cp -r skills/xir ~/.claude/skills/
```

The skill needs the `xir` package available to the agent's Python:

```bash
pip install xir
```

## Contents

```text
xir/
├── SKILL.md                       the workflow and the mental model
├── references/
│   ├── ontology.md                every primitive, id prefix, edge relation
│   ├── cli.md                     full command surface with output shapes
│   ├── patterns.md                12 worked end-to-end recipes
│   ├── authoring.md               how to write a model worth having
│   └── troubleshooting.md         every error message, explained
└── scripts/
    └── xir_health.py              one-shot model health report
```

`SKILL.md` is deliberately short. It carries the mental model, the command table and
the discipline rules; the references carry the depth, so an agent loads only what
its current task needs.

## What it teaches

1. **Traverse, do not search.** A behavioural question is a graph walk:
   `Component → Interaction → Capability → Permission → Mutation → Event →
   StateTransition`. Grepping for strings is the failure mode this skill exists to
   prevent.
2. **Conceive before coding.** Ordered workflow from intent and domain through
   authorization, capabilities, behaviour, UI and flows, then compile.
3. **Keep certainty honest.** `requirement` vs `observation` vs `inference` with
   confidence and evidence, so a guess never hardens into a fact.
4. **Change through validated transactions.** `xir patch` rolls back rather than
   leaving a half-valid model, and refuses deletions that would orphan references.
5. **Claim only what you measured.** XIR's own benchmarks are labelled
   MEASURED / SIMULATED / INFERRED; the skill tells agents not to overstate them.

## The health script

```bash
python skills/xir/scripts/xir_health.py app.xir
```

Reports validity, counts, **specification coverage** (how many capabilities declare
typed mutations, how many machines have transitions, how many interactions are fully
wired), provenance distribution, round-trip stability and context cost.

It is the fastest way to see the difference that matters:

```text
  ProjectManager [exp.projectManager] v1        # fully specified
  coverage:
    capabilities_typed                 2/2
    machines_with_transitions          3/3
    flow_steps_fully_specified         2/2

  Todo [exp.todo]                               # valid, but barely specified
  coverage:
    capabilities_typed                 1/2
    machines_with_transitions          0/1
    flow_steps_fully_specified         0/2
```

Both validate clean. Only one can answer questions about behaviour. That gap is the
thing the report is for.

Exit codes: `0` clean, `1` findings, `2` unparseable. `--json` for machine output.

## License

AGPLv3+, matching XIR.
