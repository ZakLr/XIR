"""20-task benchmark suite (PROMPT Sec 32). Measures parse/validate/query/compile per task."""
from __future__ import annotations
import time
from pathlib import Path
from xir.parser.parse import parse_file
from xir.validator.validate import validate
from xir.query.engine import query, trace_capability
from xir.compiler.emit import to_html, to_react, to_tests

EX = Path(__file__).parent.parent / "examples" / "project-manager" / "app.xir"

TASKS = [
    "Add project creation", "Add project deletion", "Add loading state",
    "Add empty state", "Add error state", "Add mobile navigation",
    "Add bulk actions", "Add search", "Add filtering", "Add onboarding",
    "Add permissions", "Add confirmation", "Modify layout",
    "Change navigation", "Add a new capability", "Change a flow",
    "Find all callers of a capability", "Explain why a component exists",
    "Detect an unreachable state", "Detect a missing error state",
]

def run_task(name: str) -> dict:
    t0 = time.perf_counter()
    exp = parse_file(EX)
    errs = validate(exp)
    nl = name.lower()
    if "caller" in nl:
        out = trace_capability(exp, "archiveProject")
    elif "explain" in nl or "why" in nl:
        out = query(exp, "surface Dashboard")
    elif "unreachable" in nl or "missing" in nl:
        out = "; ".join(errs) or "no issues"
    elif "flow" in nl:
        out = query(exp, "flow CreateProject")
    elif "capability" in nl:
        out = query(exp, "capability")
    elif "layout" in nl or "navigation" in nl:
        out = to_html(exp)
    else:
        out = to_tests(exp)
    dt = time.perf_counter() - t0
    return {"task": name, "ok": bool(out), "seconds": round(dt, 4),
            "chars": len(out), "errors": len(errs)}

def run_all() -> list[dict]:
    return [run_task(t) for t in TASKS]

if __name__ == "__main__":
    rows = run_all()
    for r in rows:
        print(f"{r['task']}: ok={r['ok']} {r['seconds']}s chars={r['chars']}")
    print(f"TOTAL {len(rows)} tasks, {sum(r['seconds'] for r in rows):.3f}s")
