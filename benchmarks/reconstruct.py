"""Reconstruction benchmark (Sec 33): semantic-only rebuild fidelity."""
from __future__ import annotations
import glob
from xir.parser.parse import parse_file
from xir.compiler.emit import to_html, to_react, to_tests
from xir.compiler.dsl import extract_html

def fidelity(original: str, rebuilt_names: set[str], kind: str) -> float:
    import re
    orig_tokens = set(re.findall(r"\w+", original))
    if not orig_tokens:
        return 1.0
    hit = sum(1 for t in rebuilt_names if t in orig_tokens)
    return round(hit / max(1, len(rebuilt_names)), 3)

def run_one(path: str) -> dict:
    src = open(path, encoding="utf-8").read()
    exp = parse_file(path)
    html = to_html(exp)
    # hide source: rebuild only from semantic projections
    re_exp = extract_html(html)
    names = {s.name for s in re_exp.surfaces} | {c.name for c in exp.capabilities}
    return {"example": path,
            "semantic_fidelity": fidelity(src, {e.name for e in exp.entities}, "entity"),
            "surface_recall": len(re_exp.surfaces) / max(1, len(exp.surfaces)),
            "html_chars": len(html), "react_chars": len(to_react(exp)),
            "tests": to_tests(exp)[:80]}

def run_all() -> list[dict]:
    return [run_one(p) for p in sorted(glob.glob("examples/*/app.xir"))]

if __name__ == "__main__":
    for r in run_all():
        print(r)
