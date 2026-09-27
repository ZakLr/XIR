"""End-to-end check of the real stdio MCP server.

Spawns the server as a subprocess, speaks the MCP protocol to it, and calls tools.
This is the test that catches a broken transport, which the in-process tests
cannot. It needs the optional `mcp` package, which `.[dev]` installs.
"""
from __future__ import annotations

import shutil
import sys

import pytest

pytest.importorskip("mcp.client.stdio")
pytest.importorskip("anyio")

MODEL = "examples/project-manager/app.xir"


def _server_argv() -> "list[str]":
    """How to launch the server, with the model argument either way.

    The installed console script when it is on PATH (as it is in CI), otherwise
    the module. Both paths must receive the model, because it is a required
    positional argument.
    """
    exe = shutil.which("xir-mcp")
    if exe:
        return [exe, MODEL]
    return [sys.executable, "-m", "xir.mcp_server", MODEL]


@pytest.mark.anyio
async def test_stdio_server_lists_and_calls_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    argv = _server_argv()
    params = StdioServerParameters(command=argv[0], args=argv[1:])

    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            init = await session.initialize()
            info = getattr(init, "server_info", None) or init.serverInfo
            assert info.name == "xir"

            listed = await session.list_tools()
            names = {t.name for t in listed.tools}
            assert {"xir_summary", "xir_trace", "xir_health"} <= names
            assert len(names) == 9

            trace = await session.call_tool("xir_trace", {"ref": "archiveProject"})
            assert "project.archive" in trace.content[0].text

            health = await session.call_tool("xir_health", {})
            assert "capabilities_typed" in health.content[0].text

            # the Literal annotation makes the SDK validate targets itself, so a
            # bad one comes back as an error result and never reaches the tool
            # body. The in-process ValueError path is covered in test_mcp.py.
            bad = await session.call_tool("xir_compile", {"target": "swiftui"})
            assert getattr(bad, "isError", False) or getattr(bad, "is_error", False)


@pytest.mark.anyio
async def test_console_script_requires_a_model():
    """The model is a required positional argument; without it the server must
    exit rather than hang waiting on stdin."""
    import subprocess

    exe = shutil.which("xir-mcp")
    argv = [exe] if exe else [sys.executable, "-m", "xir.mcp_server"]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    assert r.returncode != 0
    assert "model" in (r.stderr + r.stdout).lower()
