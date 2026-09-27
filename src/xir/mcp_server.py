"""An MCP server that exposes a XIR model as agent tools.

    xir-mcp path/to/app.xir

So an agent with a product model can ask about it without shelling out to the CLI
or learning the query syntax. The point is that the *semantics* are the interface:
`trace_capability` answers by traversal, not by string matching, so the answer is
the model's actual claim rather than a grep hit.

Tools
-----
xir_summary      what the product is, at a chosen context level
xir_validate     every semantic inconsistency
xir_trace        the full behavioural chain for a capability
xir_inspect      one node and its typed relations
xir_query        routed query: who-can, affected, lists
xir_follow       structural traversal along one relation
xir_diff         semantic diff between two models
xir_compile      a projection: react, html, a2ui, docs, a11y, playwright
xir_health       validity, specification coverage, provenance, cost

Run `python -m xir.mcp_server --help` for stdio transport details. Requires the
optional `mcp` package; the tool functions work without it, so they are testable.
"""
from __future__ import annotations

import json
import typing
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field

import xir.ir as XIR
from xir import __version__
from xir.semantic.graph import build_graph
from xir.query import engine as Q
from xir.validator.validate import validate
from xir.diff.diff import diff as semantic_diff
from xir.compiler import emit as E
from xir.compiler.dsl import to_xir
from xir.semantic.levels import summarize


class ModelServer:
    """All tool implementations, over one model. Transport-agnostic."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.model = XIR.load_file(self.path)
        self.graph = build_graph(self.model)

    # ---------- reads ----------
    def summary(self, level: int = 2) -> str:
        return summarize(self.model, int(level))

    def validate(self) -> dict[str, Any]:
        findings = validate(self.model)
        return {
            "valid": not findings,
            "count": len(findings),
            "findings": [{"code": f.code, "message": f.message, "subject": f.subject}
                         for f in findings],
        }

    def trace(self, ref: str) -> str:
        return Q.trace(self.graph, ref)

    def inspect(self, ref: str) -> str:
        return Q.show(self.graph, ref)

    def query(self, phrase: str) -> str:
        return Q.query(self.graph, phrase)

    def follow(self, ref: str, relation: str, depth: int = 1) -> str:
        return Q.follow(self.graph, ref, relation, int(depth))

    def diff(self, other_path: str) -> str:
        return semantic_diff(self.model, XIR.load_file(other_path))

    # ---------- projections ----------
    def compile(self, target: str) -> str:
        return E.emit(self.model, target)

    def health(self) -> dict[str, Any]:
        caps = list(self.model.capabilities.values())
        machines = list(self.model.machines.values())
        nodes = [i for i in self.model.all_ids() if self.model.get(i) is not None]
        with_prov = [i for i in nodes
                     if getattr(self.model.get(i), "provenance", None)
                     and self.model.get(i).provenance.source]
        typed = [c for c in caps if c.mutates or c.emits or c.requires]
        machines_t = [m for m in machines if m.transitions]
        return {
            "id": self.model.id,
            "name": self.model.name,
            "version": self.model.version or None,
            "valid": not validate(self.model),
            "nodes": len(nodes),
            "transitions": len(self.model.transitions),
            "coverage": {
                "capabilities_typed": f"{len(typed)}/{len(caps)}",
                "machines_with_transitions": f"{len(machines_t)}/{len(machines)}",
                "nodes_with_provenance": f"{len(with_prov)}/{len(nodes)}",
            },
            "provenance": {k: len([s for s in self.model.meta.values() if s.kind == k])
                           for k in ("requirement", "observation", "decision",
                                     "assumption", "inference", "proposal")},
            "chars": {"xir": len(to_xir(self.model)),
                      "json": len(self.model.model_dump_json())},
        }


# ------------------------------------------------------------- tool functions
# These signatures are the single source of truth for the wire schema. The MCP
# SDK derives `inputSchema` from them, so the offline `--list-tools` output and
# the running server cannot drift apart.

def make_tools(m: "ModelServer") -> "list[tuple[str, str, Any]]":
    """Return `(name, title, function)` for every tool, bound to one model.

    The annotations are written out in full rather than via local aliases:
    `from __future__ import annotations` makes them strings, and
    `typing.get_type_hints` resolves them against module globals only.
    """
    def xir_summary(level: Annotated[
        int, Field(2, ge=0, le=6, description=(
            "Context level. 0 names the product; higher levels add entities, "
            "capabilities, flows, surfaces, components and state machines."))
    ] = 2) -> str:
        """What this product is, projected at a chosen context level. Start here:
        it is the cheapest way to orient before asking a specific question."""
        return m.summary(level)

    def xir_validate() -> str:
        """Every semantic inconsistency in the model: unresolved references,
        unreachable states, missing confirmation before a destructive action,
        unauthorised capabilities, unsupported confidence. Run this before
        trusting any answer from this model."""
        return json.dumps(m.validate(), indent=2)

    def xir_trace(ref: str) -> str:
        """The full behavioural chain for a capability: input, required
        permission, consumption, mutation, emitted event, whether it exposes a
        component, which flows use it, which states it affects. This answers
        'what happens when the user does X' by traversal, not by matching text.
        Accepts an id, a name, or a kind.name reference."""
        return m.trace(ref)

    def xir_inspect(ref: str) -> str:
        """One node and its outgoing typed relations. Use for surfaces,
        components, state machines, flows, entities and any non-capability
        node."""
        return m.inspect(ref)

    def xir_query(phrase: str) -> str:
        """Answer a question by traversal. Understands 'who can <capability>',
        'affected <ref>', 'what happens when the user clicks <x>', 'show <kind>'
        and 'show <ref>'."""
        return m.query(phrase)

    def xir_follow(ref: str, relation: str, depth: Annotated[
        int, Field(1, ge=1, le=5, description=(
            "How many hops to walk along the relation."))
    ] = 1) -> str:
        """Structural traversal along one typed edge relation, such as
        'mutates', 'emits', 'invokes', 'requires' or 'exposed-by'. The
        relations are defined in spec/semantic-graph.md."""
        return m.follow(ref, relation, depth)

    def xir_diff(other_path: str) -> str:
        """Semantic diff between this model and another .xir file. A rename is
        reported as RENAMED rather than as a removal plus an addition."""
        return m.diff(other_path)

    def xir_compile(target: Literal[  # noqa: F821 - kept in step with emit.TARGETS
        "react", "html", "a2ui", "docs", "a11y", "playwright", "tests", "xir"]) -> str:
        """Render the model as code or documentation. 'react' emits components,
        state machines, interactions and capability calls; 'playwright' emits
        behaviour tests; 'a2ui' emits a UI tree; 'a11y' emits an audit."""
        return m.compile(target)

    def xir_health() -> str:
        """Validity plus specification coverage: how many capabilities declare
        typed mutations, how many machines have transitions, how many nodes
        carry provenance. A model can validate clean and still be barely
        specified, and this is what exposes that gap."""
        return json.dumps(m.health(), indent=2)

    return [
        ("xir_summary", "Product summary", xir_summary),
        ("xir_validate", "Validate the model", xir_validate),
        ("xir_trace", "Trace a capability", xir_trace),
        ("xir_inspect", "Inspect a node", xir_inspect),
        ("xir_query", "Routed query", xir_query),
        ("xir_follow", "Follow a relation", xir_follow),
        ("xir_diff", "Diff two models", xir_diff),
        ("xir_compile", "Compile a projection", xir_compile),
        ("xir_health", "Model health report", xir_health),
    ]


# ------------------------------------------------------------------ dispatch
def call(m: "ModelServer", name: str, args: "dict | None") -> str:
    """Dispatch a tool call. Transport-agnostic, so it is directly testable."""
    fns = {n: f for n, _, f in make_tools(m)}
    if name not in fns:
        raise KeyError(f"unknown tool {name!r}")
    return fns[name](**(args or {}))


# ------------------------------------------------------- offline tool schema
def tool_schema(m: "ModelServer") -> list[dict]:
    """The schema the server will serve, derived from the real signatures.
    Works without the `mcp` package, so `xir-mcp --list-tools` needs no extras.
    """
    import inspect

    hints = {}
    out = []
    for name, title, fn in make_tools(m):
        try:
            hints.update(typing.get_type_hints(fn, include_extras=True))
        except Exception:  # pragma: no cover - defensive
            pass
        props: dict = {}
        required: list = []
        for p in inspect.signature(fn).parameters.items():
            pname, param = p
            if param.default is inspect.Parameter.empty:
                required.append(pname)
            props[pname] = _json_type(hints.get(pname, str))
        out.append({"name": name, "title": title,
                    "description": (fn.__doc__ or "").strip(),
                    "inputSchema": {"type": "object", "properties": props,
                                    "required": required}})
    return out


def _json_type(hint) -> dict:
    """Map a Python annotation onto a JSON-schema fragment."""
    if typing.get_origin(hint) is Annotated:
        hint = hint.__origin__          # drop the FieldInfo metadata
    origin = typing.get_origin(hint)
    if origin is typing.Literal:
        return {"type": "string", "enum": list(typing.get_args(hint))}
    if origin is typing.Union:  # PEP 604 X | Y
        return {"anyOf": [_json_type(a) for a in typing.get_args(hint)]}
    return {"type": {int: "integer", str: "string", bool: "boolean",
                     float: "number"}.get(hint, "string")}


# ---------------------------------------------------------------- MCP transport
def build_app(m: "ModelServer"):
    """Create the MCPServer. Requires the optional `mcp` package (>=2)."""
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "The MCP server needs the optional 'mcp' package (>=2.0):\n"
            "    pip install 'xir-core[mcp]'\n"
            f"(import failed: {exc})")

    app = MCPServer(
        name="xir",
        instructions=(
            "This product is described by a XIR semantic model. Ask questions "
            "through these tools rather than reading code. xir_summary to "
            "orient, xir_trace for 'what happens when the user does X', "
            "xir_query for 'who can' and 'affected', xir_validate before "
            "trusting an answer, and xir_health to see how well specified the "
            "model actually is."),
        version=__version__)
    for name, title, fn in make_tools(m):
        app.add_tool(fn, name=name, title=title,
                     description=(fn.__doc__ or "").strip(),
                     structured_output=False)
    return app


def serve(path: "str | Path") -> None:
    """Run the stdio MCP server. Requires the optional `mcp` package (>=2)."""
    build_app(ModelServer(path)).run("stdio")


def _console() -> None:  # pragma: no cover
    """`xir-mcp <model>` entry point."""
    import argparse

    ap = argparse.ArgumentParser(
        prog="xir-mcp", description="Expose a XIR model as MCP tools")
    ap.add_argument("model", type=Path, help="path to a .xir model")
    ap.add_argument("--list-tools", action="store_true",
                    help="print the tool schema and exit (needs no extras)")
    ns = ap.parse_args()
    if ns.list_tools:
        print(json.dumps(tool_schema(ModelServer(ns.model)), indent=2))
    else:
        serve(ns.model)


if __name__ == "__main__":  # pragma: no cover
    _console()


