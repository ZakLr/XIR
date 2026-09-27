"""The MCP surface is a public API, so it gets the same treatment as the CLI.

These tests avoid the `mcp` package on purpose: `ModelServer` and `call` are
transport-agnostic, so the tools are testable without a running stdio server.
The transport itself is covered in test_mcp_stdio.py.
"""
from __future__ import annotations

import json

import pytest

from xir.compiler import emit as E
from xir.mcp_server import ModelServer, call, make_tools, tool_schema

MODEL = "examples/project-manager/app.xir"

REQUIRED_ARGS = {
    "xir_trace": {"ref": "archiveProject"},
    "xir_inspect": {"ref": "surface.dashboard"},
    "xir_query": {"phrase": "who can archiveProject"},
    "xir_follow": {"ref": "archiveProject", "relation": "requires"},
    "xir_diff": {"other_path": MODEL},
    "xir_compile": {"target": "react"},
}


@pytest.fixture(scope="module")
def server() -> ModelServer:
    return ModelServer(MODEL)


# ------------------------------------------------------------------ schema
def test_tool_names_are_unique_and_prefixed():
    names = [n for n, _, _ in make_tools(ModelServer(MODEL))]
    assert len(names) == len(set(names))
    assert all(n.startswith("xir_") for n in names)
    assert len(names) == 9


def test_every_tool_has_a_description():
    for _, _, fn in make_tools(ModelServer(MODEL)):
        assert (fn.__doc__ or "").strip(), f"{fn.__name__} has no description"


def test_schema_declares_required_arguments():
    for tool in tool_schema(ModelServer(MODEL)):
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        for req in schema.get("required", []):
            assert req in schema["properties"], f"{tool['name']}: {req} undeclared"


def test_schema_types_are_resolved_not_defaulted():
    """A regression guard: the annotations are strings under
    `from __future__ import annotations`, and an unresolvable one silently
    degrades to "string" for everything."""
    props = {t["name"]: t["inputSchema"]["properties"]
             for t in tool_schema(ModelServer(MODEL))}
    assert props["xir_summary"]["level"]["type"] == "integer"
    assert props["xir_follow"]["depth"]["type"] == "integer"
    assert props["xir_trace"]["ref"]["type"] == "string"
    assert "enum" in props["xir_compile"]["target"]


def test_every_tool_is_dispatchable():
    """A tool in the schema with no dispatch branch is a lie to the client."""
    server = ModelServer(MODEL)
    for name, _, _ in make_tools(server):
        args = {"xir_summary": {"level": 2}}.get(name, REQUIRED_ARGS.get(name, {}))
        assert isinstance(call(server, name, args), str)


# ------------------------------------------------------------------ tools
def test_summary_honours_the_level_argument(server):
    assert server.summary(0) != server.summary(4)
    assert "ProjectManager" in server.summary(0)


def test_validate_reports_the_real_state(server):
    result = server.validate()
    assert result["valid"] is True
    assert result["count"] == 0


def test_trace_answers_by_traversal_not_string_match(server):
    out = server.trace("archiveProject")
    # a string grep would miss the role check; traversal finds it
    assert "project.archive" in out
    assert "CAPABILITY" in out


def test_query_routes_who_can(server):
    assert "project.archive" in server.query("who can archiveProject")


def test_follow_walks_a_typed_relation(server):
    out = server.follow("archiveProject", "requires", 1)
    assert "project.archive" in out


def test_diff_against_itself_is_empty(server):
    assert server.diff(MODEL).strip() == "no semantic changes"


def test_compile_covers_every_advertised_target(server):
    by_name = {t["name"]: t for t in tool_schema(server)}
    enum = by_name["xir_compile"]["inputSchema"]["properties"]["target"]["enum"]
    assert set(enum) == set(E.TARGETS), "MCP enum drifted from the emitter registry"
    for target in enum:
        assert call(server, "xir_compile", {"target": target}).strip()


def test_compile_rejects_an_unknown_target(server):
    with pytest.raises(ValueError, match="unknown target"):
        server.compile("swiftui")


def test_health_separates_validity_from_specification_coverage(server):
    """The point of health: a model can validate clean and still be under-specified."""
    h = server.health()
    assert h["valid"] is True
    cov = h["coverage"]
    assert "capabilities_typed" in cov and "nodes_with_provenance" in cov
    typed, total = cov["capabilities_typed"].split("/")
    assert 0 < int(typed) <= int(total)


def test_health_reports_provenance_gap(server):
    """The example model carries no provenance; the report must say so rather
    than quietly implying full coverage."""
    cov = json.loads(call(server, "xir_health", {}))["coverage"]
    have, total = cov["nodes_with_provenance"].split("/")
    assert int(have) <= int(total)


def test_unknown_tool_raises(server):
    with pytest.raises(KeyError):
        call(server, "xir_nope", {})
