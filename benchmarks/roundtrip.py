"""Round-trip stability (Sec 34): DSL -> canonical -> reparse == semantically stable."""
from __future__ import annotations
import glob
from xir.parser.parse import parse_file, parse_text
from xir.compiler.dsl import to_xir
from xir.diff.diff import diff

def semantic_equal(a: str, b: str) -> bool:
    return diff(parse_file(a), parse_text(open(b, encoding="utf-8").read())) == "no semantic changes"

def run_one(path: str, tmp: str = "_rt_tmp.xir") -> dict:
    exp = parse_file(path)
    canon = to_xir(exp)
    open(tmp, "w", encoding="utf-8").write(canon)
    stable = semantic_equal(path, tmp)
    import os
    os.remove(tmp)
    return {"example": path, "stable": stable, "canon_chars": len(canon)}

def run_all() -> list[dict]:
    return [run_one(p) for p in sorted(glob.glob("examples/*/app.xir"))]

if __name__ == "__main__":
    rows = run_all()
    for r in rows:
        print(r)
    print("STABLE" if all(r["stable"] for r in rows) else "UNSTABLE")
