# Changelog

## 1.0.0 (2026-09-27)
- Brand: XIR (renamed from IXL), AGPLv3+ license.
- Strict Lark grammar + tolerant fallback parser; canonical emitter; round-trip stable.
- Semantic graph (NetworkX, L0–L6), query/inspect/explain/trace, full patch ops, semantic diff.
- Validator: Sec-47 checks + provenance/version rules.
- Emitters: HTML, React, A2UI, docs, a11y, Playwright, tests.
- CLI: `xir parse|validate|query|inspect|explain|diff|compile|test|bench|patch` (`ixl` alias kept).
- 5 examples with goldens; 20-task + reconstruction + round-trip + baseline-proxy benchmarks.
