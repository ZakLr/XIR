# Releasing

Repo: https://github.com/ZakLr/XIR · License: AGPLv3+ · CLI: `xir`

## Before a release

```bash
pytest -q                    # 64 tests
python benchmarks/tasks.py   # semantic benchmark, must be all-pass
python -m build --wheel      # then verify the artifact in a clean env:
python -m venv /tmp/v && /tmp/v/bin/pip install dist/*.whl \
  && /tmp/v/bin/xir validate examples/project-manager/app.xir
```

The wheel check matters: the grammar is loaded from package data at runtime, so a
wheel that omits `grammar.lark` installs fine and then fails on first use. CI does
this on every push.

## Publish to GitHub

```bash
git add -A
git commit -m "..."
git tag v0.3.0
git push origin main --tags
```

Repo settings: description "The semantic IR for interactive products", topics
`dsl ir agents mcp a2ui compiler ux semantic-model`, Issues + Security Advisories
enabled.

## Publish to PyPI

```bash
pip install build twine
python -m build
twine upload --repository testpypi dist/*   # test first
twine upload dist/*
```

## What is public

Tracked: `src/`, `tests/`, `spec/`, `research/`, `docs/`, `examples/`, `benchmarks/`,
community files (`LICENSE`, `README`, `CHANGELOG`, `CONTRIBUTING`, `SECURITY`,
`CODE_OF_CONDUCT`, `RELEASING`), and CI config.

## What is private

`.private/` holds the personal briefs, prompts and scratch notes. It is git-ignored
and never published. The public equivalents are `spec/`, `research/`, `docs/`,
`DECISIONS.md` and `OPEN_QUESTIONS.md`. Delete `.private/` before publishing a fork.
