#!/usr/bin/env python3
"""Build the documentation site.

    python branding/build_site.py            # stage + build
    python branding/build_site.py --serve    # live-reload server

The site renders the markdown that already lives in the repo, so documentation
cannot drift from the code. This script stages those files into `.site-src/`,
**mirroring the repository layout** so that every relative link keeps working
in both GitHub and on the site, then hands off to mkdocs.

Nothing is duplicated in version control: `.site-src/` and `site/` are build
artifacts and are git-ignored.
"""
from __future__ import annotations
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / ".site-src"

# whole trees, copied with their layout intact
TREES = ["spec", "research", "benchmarks", "docs", "skills"]
# individual files that live at the repo root
# The GitHub landing page is not staged: the generated index.md is the site
# home, and the two would collide.
ROOT_FILES = ["DECISIONS.md", "OPEN_QUESTIONS.md", "CHANGELOG.md",
              "CONTRIBUTING.md", "LICENSE"]
# The site home is the same file GitHub renders, with its `../` prefixes
# rewritten, because the home sits at the site root while the file lives in
# docs/. One source of truth: `docs/index.md`.
HOME = "docs/index.md"


def _stage_home() -> None:
    """Write the repo's docs/index.md to the site root, un-prefixing relative
    links so they resolve from the root rather than from docs/."""
    src = (ROOT / HOME).read_text(encoding="utf-8")
    src = re.sub(r"\]\(\.\./(?=[^/])", "](", src)   # ../foo  -> foo
    src = re.sub(r"\]\(\.\./([^)/]+)/", r"](/", src)  # ../d/f -> d/f
    (STAGE / "index.md").write_text(src, encoding="utf-8")


SKIP_RELPATHS = {
    "xir/scripts",                 # the health script is run, not rendered
    "xir/SKILL.md",                # the skill body; its nav entry lives in nav
}
SKIP_NAMES = {"__init__.py", "harness.py", "tasks.py", "baseline.py",
              "roundtrip.py", "reconstruct.py", "_frame.png"}


def _copytree(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src).as_posix()
        if any(p.startswith(".") for p in item.parts):
            continue
        if item.suffix == ".pyc" or item.name in SKIP_NAMES:
            continue
        if any(rel == s or rel.startswith(s + "/") for s in SKIP_RELPATHS):
            continue
        # the generated site home supersedes these twins
        if src.name == "docs" and rel in {"README.md", "index.md"}:
            continue
        target = dst / item.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def stage() -> int:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    for tree in TREES:
        src = ROOT / tree
        if src.is_dir():
            _copytree(src, STAGE / tree)
    for f in ROOT_FILES:
        src = ROOT / f
        if src.is_file():
            shutil.copy2(src, STAGE / f)
    _stage_home()

    n = sum(1 for _ in STAGE.rglob("*.md"))
    print(f"  staged {n} markdown files into {STAGE.name}/")
    return 0


def main() -> int:
    if stage():
        return 1
    serve = "--serve" in sys.argv
    cmd = [sys.executable, "-m", "mkdocs", "build"] + (["--strict"] if not serve else []) 
    if serve:
        cmd.append("serve")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode == 0 and not serve:
        print(f"  site -> {ROOT / 'site' / 'index.html'}")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
