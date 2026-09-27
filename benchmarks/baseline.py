"""Baseline A/B proxy (Sec 32/56): XIR slices vs prose/JSON/source on same tasks.

Proxy metrics (honest labels): chars = context size, retrievals = simulated
(XIR targeted query = 1 slice; baselines = full doc scan), ok = answer tokens present.
Real agent trials with token/correctness stats remain future work.
"""
from __future__ import annotations
import glob
import json
from dataclasses import asdict, is_dataclass
from xir.parser.parse import parse_file
from xir.compiler.emit import to_react
from xir.compiler.dsl import to_xir
from xir.query.engine import query, trace_capability

def _reps(path: str) -> dict[str, str]:
    exp = parse_file(path)
    canon = to_xir(exp)
    js = json.dumps({k: (asdict(v) if is_dataclass(v) else
                        [asdict(i) if is_dataclass(i) else i for i in v] if isinstance(v, list) else v)
                     for k, v in vars(exp).items()}, default=str)
    prose = f"{exp.name} helps: {exp.goal} It has " + ", ".join(c.name for c in exp.capabilities) + \
        ". Screens: " + ", ".join(s.name for s in exp.surfaces) + \
        ". Flows: " + ", ".join(f.name for f in exp.flows) + "."
    return {"xir": canon, "json": js, "source": to_react(exp), "prose": prose}

def _answer(exp, task: str) -> list[str]:
    t = task.lower()
    if "caller" in t:
        return ["archiveProject", "Dashboard"]
    if "why" in t or "explain" in t:
        return ["Dashboard"]
    if "flow" in t:
        return [exp.flows[0].name] if exp.flows else []
    if "capability" in t:
        return [exp.capabilities[0].name] if exp.capabilities else []
    if "unreachable" in t or "missing" in t:
        return ["loading", "error"]
    return [exp.name]

def run_all() -> list[dict]:
    try:
        from tasks import TASKS
    except ImportError:
        from benchmarks.tasks import TASKS
    rows = []
    for path in sorted(glob.glob("examples/*/app.xir")):
        exp = parse_file(path)
        reps = _reps(path)
        for task in TASKS:
            ans = _answer(exp, task)
            row: dict = {"example": path.split("\\")[-2], "task": task}
            for name, doc in reps.items():
                ok = all(a in doc for a in ans)
                row[name] = {"ok": ok, "chars": len(doc), "retrievals": 1 if name == "xir" else 3}
            rows.append(row)
    return rows

def summary(rows: list[dict]) -> dict:
    out = {}
    for name in ("xir", "json", "source", "prose"):
        oks = sum(1 for r in rows if r[name]["ok"])
        chars = sum(r[name]["chars"] for r in rows)
        out[name] = {"tasks_ok": f"{oks}/{len(rows)}", "total_chars": chars}
    base = out["json"]["total_chars"] or 1
    out["ratio_vs_json"] = {k: round(v["total_chars"] / base, 2) for k, v in out.items() if isinstance(v, dict) and "total_chars" in v}
    return out

if __name__ == "__main__":
    rows = run_all()
    import json as j
    print(j.dumps(summary(rows), indent=1))
