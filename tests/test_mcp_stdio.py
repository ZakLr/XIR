"""End-to-end check of the real stdio MCP server.

Spawns `xir-mcp` as a subprocess, speaks the MCP protocol to it, and calls a tool.
This is the test that would catch a broken transport, which the in-process tests
cannot. Needs the optional `mcp` package: pip install -e '.[mcp]'
"""
from __future__ import annotations

import shutil
import sys

import pytest

mcp_client = pytest.importorskip("mcp.client.stdio")
pytest.importorskip("anyio")

MODEL = "examples/project-manager/app.xir"


def _server_argv() -> list[str]:
    # prefer the installed console script; fall back to the module
    exe = shutil.which("xir-mcp")
    return [exe] if exe else [sys.executable, "-m", "xir.mcp_server"]


@pytest.mark.anyio
async def test_stdio_server_lists_and_calls_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=_server_argv()[0] if len(_server_argv()) == 1
                                    else sys.executable,
                                    args=[] if len(_server_argv()) == 1 else ["-m", "xir.mcp_server", MODEL],
                                    env=None)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            init = await session.initialize()
            assert getattr(init, "server_info", None) or init.serverInfo
            assert (getattr(init, "server_info", None) or init.serverInfo).name == "xir"

            listed = await session.list_tools()
            names = {t.name for t in listed.tools}
            assert {"xir_summary", "xir_trace", "xir_health"} <= names
            assert len(names) == 9

            result = await session.call_tool("xir_trace", {"ref": "archiveProject"})
            text = result.content[0].text
            assert "project.archive" in text

            health = await session.call_tool("xir_health", {})
            assert "capabilities_typed" in health.content[0].text
