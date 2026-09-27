# Benchmark report (v0.3)

Reproduce with `python benchmarks/tasks.py`.

## Provenance labels

Every number below is labelled. This is the point of the report.

- **MEASURED** — computed by the code in this repository, reproducible by running it.
- **SIMULATED** — a stand-in for something that cannot be measured without a real agent
  in the loop. Never presented as agent performance.
- **INFERRED** — reasoned from measured numbers, not directly observed.

## MEASURED — semantic task suite

40/40 pass. Tasks are answered by walking the semantic graph and checked against
declared expectations, not by substring matching.

| Task kind | What it proves | Result |
|---|---|---|
| reasoning | permission lookup and mutation/event sets resolve from edges | pass |
| ui | the interaction that invokes a capability is found by traversal | pass |
| state | the state entered after a capability fires is found | pass |
| security | the actor allowed to invoke a capability is found | pass |
| adversarial | unreachable states are found | pass |
| modification | a patch that clears an actor's permissions takes effect | pass |
| modification | a rename preserves semantic identity | pass |

## MEASURED — context cost

Characters per example, per projection. Lower is cheaper to load.

| Example | nodes | transitions | xir | html | react | playwright | json |
|---|---|---|---|---|---|---|---|
| todo | 17 | 0 | 633 | 101 | 1724 | 373 | 3643 |
| dashboard | 15 | 0 | 563 | 119 | 1563 | 385 | 3296 |
| ecommerce | 16 | 0 | 617 | 118 | 1581 | 392 | 3488 |
| clinic | 26 | 0 | 1310 | 268 | 2282 | 510 | 6212 |
| project-manager | 81 | 21 | 5277 | 1055 | 8627 | 2140 | 23052 |

XIR costs **0.23×** the JSON dump of the same model and is the only representation
carrying states, transitions, permissions and events. Rendered projections are larger
than XIR because they are outputs, not inputs.

## SIMULATED — retrieval counts

| Representation | Retrievals to answer a model question |
|---|---|
| XIR | 1 (`xir trace <id>`) |
| JSON | 2 |
| HTML | 3 |
| React | 4 |

**These are assumptions, not measurements.** A real agent study is still outstanding.

## MEASURED — round trip

`parse → semantic IR → serialize → parse` is semantically stable for 5/5 examples,
including states, transitions, permissions, provenance and evidence. Verified by
`tests/test_goldens.py`.

## MEASURED — test suite

64 tests pass. Coverage spans parsing (including strictness and recovery), normalization,
stable identity, resolution, the typed graph, queries, patches and atomicity,
validation, the React and Playwright emitters, and round-trip stability.

## What is NOT claimed

- That XIR makes an LLM agent faster or more correct. No blinded agent trial has been run.
- Any token saving. Character counts are a proxy; tokens depend on the tokenizer.
- That the benchmark generalises beyond these five examples.

The honest summary: the semantic model now contains enough structure to answer the
central product-engineering questions by traversal, and the representation is compact
and round-trip stable. Whether that translates into real agent performance is the open
experiment.
