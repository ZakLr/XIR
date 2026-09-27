# Releasing / publishing (repo: https://github.com/ZakLr/XIR)

1. URLs set. Verify: `pytest -q && python benchmarks/roundtrip.py` — green + STABLE.
2. `git init && git add -A && git commit -m "XIR 1.0.0"` (if not already a repo).
3. `git remote add origin https://github.com/ZakLr/XIR.git`, `git push -u origin main`.
4. In repo settings: description “The semantic IR for interactive products”,
   topics: `dsl ir agents mcp a2ui compiler ux semantic-model`,
   enable Issues + Security Advisories, add `LICENSE` detection check.
5. Tag: `git tag v1.0.0 && git push --tags`. Optional: `pip install build && python -m build`
   + TestPyPI first, then PyPI.
