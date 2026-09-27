# Benchmarks (methodology)

Suite: `benchmarks/tasks.py` (20 tasks, Sec 32), `reconstruct.py` (Sec 33), `roundtrip.py` (Sec 34).
Baselines to compare: prose, JSON, source code, screenshots/context vs XIR.
Metrics: tokens (proxy: chars), context size, tool calls, completion, correctness, state/flow
correctness, UI fidelity, a11y, regressions, time.
Gate (Sec 56): A/B same modification tasks with/without XIR; expand language only on measurable win.
Current v0.2 results: 14 pytest pass; 20/20 harness tasks ok; round-trip STABLE on 5/5
examples; reconstruction surface recall 1.0/5; baseline proxy (baseline.py): XIR 93/100
answer-hit at 0.64× JSON chars. Report: `benchmarks/report.md`. Real blinded trials pending.
