#!/usr/bin/env python3
"""One-shot health report for an XIR model.

Answers, in one pass: is the model coherent, how much of it is actually specified,
where are the gaps, and what does it cost to load.

    python xir_health.py app.xir
    python xir_health.py app.xir --json
    python xir_health.py examples/*/app.xir

Exit codes: 0 clean, 1 findings, 2 the model could not be parsed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import xir.ir as XIR
    from xir.compiler.dsl import to_xir
    from xir.diff.diff import diff
    from xir.validator.validate import validate
except ImportError:  # pragma: no cover
    sys.exit("xir is not installed. Try: pip install xir")


def coverage(m) -> dict:
    """How much of the model is actually specified, not merely declared."""
    caps = list(m.capabilities.values())
    surfaces = list(m.surfaces.values())
    machines = list(m.machines.values())
    explicit_machines = [x for x in machines if x.transitions]
    typed_caps = [c for c in caps if c.mutates or c.emits or c.requires]
    wired_interactions = [i for i in m.interactions.values() if i.target and i.invokes]
    declared_steps = [s for s in m.steps.values() if s.action and s.to]
    machines_with_initial = [x for x in machines if x.initial_declared]

    def pct(n, d):
        return round(100 * n / d) if d else None

    return {
        "capabilities_typed": f"{len(typed_caps)}/{len(caps)}",
        "capabilities_typed_pct": pct(len(typed_caps), len(caps)),
        "machines_with_transitions": f"{len(explicit_machines)}/{len(machines)}",
        "machines_with_transitions_pct": pct(len(explicit_machines), len(machines)),
        "machines_declaring_initial": f"{len(machines_with_initial)}/{len(machines)}",
        "interactions_fully_wired": f"{len(wired_interactions)}/{len(m.interactions)}",
        "flow_steps_fully_specified": f"{len(declared_steps)}/{len(m.steps)}",
        "surfaces_with_states": f"{len([s for s in surfaces if s.states])}/{len(surfaces)}",
    }


def provenance(m) -> dict:
    nodes = [n for n in m.all_ids() if m.get(n) is not None]
    with_prov = [n for n in nodes if getattr(m.get(n), "provenance", None)
                 and m.get(n).provenance.source]
    statements = list(m.meta.values())
    return {
        "nodes_with_provenance": f"{len(with_prov)}/{len(nodes)}",
        "statements": len(statements),
        "by_kind": {k: len([s for s in statements if s.kind == k])
                    for k in ("requirement", "decision", "observation",
                              "assumption", "inference", "proposal")},
        "inferences": [f"{s.name} ({s.confidence})" for s in statements
                       if s.kind == "inference"],
    }


def cost(m, path: Path) -> dict:
    from xir.compiler import emit as E
    out = {
        "nodes": len(m.all_ids()),
        "transitions": len(m.transitions),
        "states": len(m.states),
        "source_chars": len(path.read_text(encoding="utf-8")),
    }
    for name, fn in (("xir", to_xir), ("json", lambda x: x.model_dump_json()),
                     ("react", E.to_react), ("playwright", E.to_playwright)):
        try:
            out[f"{name}_chars"] = len(fn(m))
        except Exception:
            out[f"{name}_chars"] = None
    return out


def report(path: Path, as_json: bool) -> tuple[int, dict]:
    try:
        m = XIR.load_file(path)
    except Exception as exc:
        return 2, {"file": str(path), "error": f"{type(exc).__name__}: {exc}"}

    findings = validate(m)
    data = {
        "file": str(path),
        "id": m.id,
        "name": m.name,
        "version": m.version or None,
        "valid": not findings,
        "findings": [{"code": f.code, "message": f.message, "subject": f.subject}
                     for f in findings],
        "counts": {k: len(getattr(m, k)) for k in
                   ("goals", "actors", "permissions", "entities", "events",
                    "capabilities", "surfaces", "components", "interactions",
                    "machines", "states", "transitions", "flows", "invariants")},
        "coverage": coverage(m),
        "provenance": provenance(m),
        "cost": cost(m, path),
    }
    try:
        data["round_trip_stable"] = diff(m, XIR.load(to_xir(m))) == "no semantic changes"
    except Exception as exc:
        data["round_trip_stable"] = False
        data.setdefault("round_trip_error", str(exc)[:200])
    return (1 if findings else 0), data


def render(rows: list[dict]) -> None:
    for d in rows:
        if "error" in d:
            print(f"{d['file']}\n  UNPARSEABLE  {d['error']}\n")
            continue
        print(f"{d['file']}")
        head = f"  {d['name']} [{d['id']}]"
        if d["version"]:
            head += f" v{d['version']}"
        print(head)
        c = d["counts"]
        print("  " + "  ".join(f"{k}={v}" for k, v in c.items() if v))
        cov = d["coverage"]
        print("  coverage:")
        for k, v in cov.items():
            if k.endswith("_pct"):
                continue
            print(f"    {k:<34} {v}")
        pr = d["provenance"]
        print(f"  provenance: {pr['nodes_with_provenance']} nodes, "
              f"statements {pr['by_kind']}")
        for inf in pr["inferences"]:
            print(f"    inference: {inf}")
        rt = "stable" if d["round_trip_stable"] else "UNSTABLE"
        print(f"  round-trip: {rt}")
        if d["valid"]:
            print("  findings: none")
        else:
            print(f"  findings: {len(d['findings'])}")
            for f in d["findings"][:20]:
                print(f"    [{f['code']}] {f['message']}")
            if len(d["findings"]) > 20:
                print(f"    ... and {len(d['findings']) - 20} more")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description="XIR model health report")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    codes, rows = [], []
    for p in args.files:
        code, data = report(p, args.json)
        codes.append(code)
        rows.append(data)

    if args.json:
        print(json.dumps(rows if len(rows) > 1 else rows[0], indent=2))
    else:
        render(rows)
    return max(codes)


if __name__ == "__main__":
    raise SystemExit(main())
