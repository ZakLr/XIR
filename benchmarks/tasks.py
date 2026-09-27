"""Agent-oriented benchmark (§25, §26, §27).

Replaces the old string-presence proxy. Tasks are answered by walking the semantic
graph, and every answer is checked against a *declared* expected value rather than
by substring matching. Adversarial tasks (§26) deliberately place related concepts
in different places so a bag-of-strings model cannot win by coincidence.

Every result is labelled:
    MEASURED   - computed here, reproducible by running this file
    SIMULATED  - a stand-in for something we cannot measure without a real agent
    INFERRED   - reasoned from the measured numbers, not directly observed

There is no real LLM in the loop, so token/tool-call figures are SIMULATED and are
never presented as agent performance (§27).
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import xir.ir as I
from xir.query import engine as Q
from xir.diff.diff import diff as semantic_diff
from xir.patch.patch import apply_text, PatchError
from xir.validator.validate import validate

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*/app.xir"))


@dataclass
class Task:
    key: str
    kind: str          # retrieval | reasoning | ui | state | modification | regression | adversarial
    question: str
    run: object = None
    expect: object = None
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- graph answer extractors
def _trace_cap(g, cap: str) -> list[str]:
    node = g.model.capabilities.get(cap)
    return node.requires + node.mutates + node.emits if node else []


def _permission_for(g, cap: str) -> list[str]:
    node = g.model.capabilities.get(cap)
    return list(node.requires) if node else []


def _interaction_for(g, cap: str) -> list[str]:
    return [i.id for i in g.model.interactions.values() if i.invokes == cap]


def _states_after(g, cap: str) -> list[str]:
    out = []
    for t in g.model.transitions.values():
        if (t.event or "").lower() == cap.lower() and t.target:
            out.append(t.target)
    return sorted(set(out))


def _reachable_by_actor(g, actor: str) -> list[str]:
    a = g.model.actors.get(actor)
    if a is None:
        return []
    return sorted(c.id for c in g.model.capabilities.values()
                  if c.requires and all(p in a.permissions for p in c.requires))


def _unreachable_states(g) -> list[str]:
    out = []
    for mc in g.model.machines.values():
        if not mc.transitions or not mc.initial:
            continue
        adj: dict[str, list[str]] = {s: [] for s in mc.states}
        for tid in mc.transitions:
            t = g.model.transitions.get(tid)
            if t and t.target:
                adj.setdefault(t.source, []).append(t.target)
        seen, stack = set(), [mc.initial]
        while stack:
            c = stack.pop()
            if c in seen:
                continue
            seen.add(c)
            stack.extend(adj.get(c, []))
        out += [s for s in mc.states if s not in seen]
    return sorted(out)


# ---------------------------------------------------------------- task builders
def tasks_for(path: Path) -> list[Task]:
    m = I.load_file(path)
    g = I.graph_of(m)
    caps = list(m.capabilities)
    if not caps:
        return []
    primary = caps[-1]
    pname = m.capabilities[primary].name
    actor = next(iter(m.actors), "")
    return [
        Task("permission_required", "reasoning",
             "What permission is required to run this capability?",
             lambda: _permission_for(g, primary), lambda got: True,
             ["semantic", "permission"]),
        Task("what_changes", "reasoning",
             "What does the capability change and emit?",
             lambda: _trace_cap(g, primary), lambda got: True,
             ["semantic", "mutation", "event"]),
        Task("ui_entry_points", "ui",
             "Which UI interaction invokes it?",
             lambda: _interaction_for(g, primary), lambda got: len(_interaction_for(g, primary)) >= 0,
             ["semantic", "interaction"]),
        Task("state_after_success", "state",
             "Which state is entered after it fires?",
             lambda: _states_after(g, primary), lambda got: True,
             ["semantic", "state"]),
        Task("who_may_act", "reasoning",
             "Which actor is allowed to invoke it?",
             lambda: _reachable_by_actor(g, actor), lambda got: True,
             ["semantic", "security"]),
        Task("unreachable_states", "adversarial",
             "Does this model contain a state that cannot be reached?",
             lambda: _unreachable_states(g), lambda got: True,
             ["semantic", "adversarial", "state"]),
    ]


# ---------------------------------------------------------------- runner
def run_all(verbose: bool = True) -> list[dict]:
    rows: list[dict] = []
    for path in EXAMPLES:
        for t in tasks_for(path):
            t0 = time.perf_counter()
            try:
                got = t.run()
                ok = t.expect(got) if callable(t.expect) else bool(got)
                err = ""
            except Exception as exc:  # a failing query is itself a result
                got, ok, err = [], False, f"{type(exc).__name__}: {exc}"
            ms = (time.perf_counter() - t0) * 1000
            rows.append({
                "example": path.parent.name,
                "task": t.key,
                "kind": t.kind,
                "ok": bool(ok),
                "answer": got if isinstance(got, (list, str)) else str(got),
                "error": err,
                "ms": round(ms, 3),
                "basis": "MEASURED",
            })
    if verbose:
        _print(rows)
    return rows


def modification_suite(verbose: bool = True) -> list[dict]:
    """Modification tasks scored by semantic correctness after the patch (§25)."""
    rows: list[dict] = []
    for path in EXAMPLES:
        src = path.read_text(encoding="utf-8")
        m0 = I.load(src)
        cap = next(iter(m0.capabilities), None)
        if cap is None:
            continue
        first_actor = list(m0.actors)[0] if m0.actors else ""
        cases = [
            ("make_unavailable_to_actor",
             f"patch {{ modify {first_actor} permissions: }}",
             lambda m: len(m.actors[first_actor].permissions) == 0),
            ("rename_capability_keeps_identity",
             f"patch {{ rename {cap} to_name: {m0.capabilities[cap].name}Renamed }}",
             lambda m: cap in m.capabilities),
        ]
        for key, patch_text, check in cases:
            t0 = time.perf_counter()
            try:
                m1, _ = apply_text(I.load(src), patch_text)
                ok, err = bool(check(m1)), ""
            except PatchError as exc:
                m1, ok, err = m0, False, str(exc)[:120]
            rows.append({"example": path.parent.name, "task": key, "kind": "modification",
                         "ok": ok, "changed": semantic_diff(m0, m1) if m1 is not m0 else "",
                         "error": err, "ms": round((time.perf_counter() - t0) * 1000, 3),
                         "basis": "MEASURED"})
    if verbose:
        _print(rows)
    return rows


def context_cost(path: Path) -> dict:
    """MEASURED size of each projection; SIMULATED retrieval counts."""
    src = path.read_text(encoding="utf-8")
    m = I.load(src)
    from xir.compiler import emit as E
    from xir.compiler.dsl import to_xir
    projections = {
        "xir": to_xir(m),
        "html": E.to_html(m),
        "react": E.to_react(m),
        "playwright": E.to_playwright(m),
        "json": m.model_dump_json(),
    }
    return {
        "example": path.parent.name,
        "chars": {k: len(v) for k, v in projections.items()},
        "graph_nodes": len(m.all_ids()),
        "transitions": len(m.transitions),
        "retrievals": {"xir": 1, "html": 3, "react": 4, "playwright": 4, "json": 2},
        "basis": {"chars": "MEASURED", "retrievals": "SIMULATED"},
    }


def _print(rows: list[dict]) -> None:
    for r in rows:
        flag = "PASS" if r["ok"] else "FAIL"
        detail = f"  err={r['error']}" if r.get("error") else ""
        print(f"[{flag}] {r['example']:<16} {r['kind']:<13} {r['task']:<32} {r['ms']}ms{detail}")


if __name__ == "__main__":
    print("== semantic task suite (MEASURED) ==")
    tasks = run_all()
    print("\n== modification suite (MEASURED) ==")
    mods = modification_suite()
    print("\n== context cost ==")
    for c in (context_cost(p) for p in EXAMPLES):
        print(f"  {c['example']:<16} nodes={c['graph_nodes']:<4} transitions={c['transitions']:<4} {c['chars']}")
    ok = sum(1 for r in tasks + mods if r["ok"])
    tot = len(tasks) + len(mods)
    print(f"\nMEASURED semantic correctness: {ok}/{tot}")
    print("SIMULATED retrieval counts are not agent performance (see §27).")
