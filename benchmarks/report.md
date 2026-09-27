# Benchmark report (v0.2, 2026-09-27)

- pytest: 14 passed (parser, validator ×6, query, diff, compile, goldens, patch ×2).
- 20-task harness (`benchmarks/tasks.py`): 20/20 ok.
- Round-trip (`benchmarks/roundtrip.py`): STABLE 5/5 examples
  (DSL → `to_xir()` canonical → reparse → `diff()` clean, incl. version/meta/provenance).
- Reconstruction (`benchmarks/reconstruct.py`): surface recall 1.0 on 5/5.
- Baseline A/B proxy (`benchmarks/baseline.py`, 5 examples × 20 tasks = 100 checks):
  XIR 93/100 answer-hit at 0.64× JSON chars; JSON 93/100 at 1.0×; React-source 82/100;
  prose 83/100 (smaller but lossier). Proxy only: chars≈context, 1 vs 3 retrievals simulated.
- All 5 examples `xir validate`: valid.
- Real blinded agent trials (tokens/time/correctness stats) remain future work per
  `research/benchmarks.md`; do not claim victory beyond proxies.
