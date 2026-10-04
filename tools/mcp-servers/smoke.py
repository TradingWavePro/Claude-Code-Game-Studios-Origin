#!/usr/bin/env python
"""Smoke-test the local MCP servers registered in the project .mcp.json.

Each server is probed with a real MCP handshake (initialize + tools/list), so a
PASS means "the server speaks MCP and answers", not "a binary exists on disk".

Usage (from the project root):

    .venv/Scripts/python.exe tools/mcp-servers/smoke.py [server ...] \
        [--call TOOL [--args '{"key": "value"}']] [--force]

With no arguments every server is probed. `--call` invokes one tool on the
first named server (default: the first server in .mcp.json) after the
handshake, which is how a real tool call gets exercised rather than just the
tool listing.

Servers whose host application must be running (Krita, Blockbench) report
DEFERRED instead of FAIL when that app is not up. `--force` skips that check
to probe the MCP server itself, which is useful for telling "the server is
broken" apart from "the host app is not running".

Exit code is 0 when every probed server passes, 1 otherwise.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MCP_CONFIG = PROJECT_ROOT / ".mcp.json"

# Servers whose host application must be running before their bridge tools can
# answer. Reported as DEFERRED rather than FAIL when that app is not up.
REQUIRES_HOST_APP = {"krita": "krita.exe", "blockbench": "Blockbench.exe"}


def load_servers() -> dict[str, dict]:
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    return config["mcpServers"]


def host_app_running(exe: str) -> bool:
    """True when a process named `exe` is currently running.

    Used to decide DEFERRED vs FAIL for the servers in REQUIRES_HOST_APP. A
    probe that cannot be run at all is reported as not running: DEFERRED is
    the non-failing state, so an unreadable process list must not turn a
    healthy server into a FAIL.
    """
    if os.name == "nt":
        try:
            listing = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/NH"],
                capture_output=True, text=True, timeout=15,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return False
        return exe.lower() in listing.lower()
    try:
        listing = subprocess.run(
            ["ps", "-A", "-o", "comm="], capture_output=True, text=True, timeout=15,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return any(Path(line.strip()).name.lower() == exe.lower() for line in listing.splitlines())


def parse_args(argv: list[str]) -> tuple[list[str], str | None, dict, bool]:
    """Split the command line into server names, an optional tool call, and force."""
    names = list(argv)
    call: str | None = None
    call_args: dict = {}
    force = "--force" in names
    names = [n for n in names if n != "--force"]

    if "--args" in names:
        idx = names.index("--args")
        call_args = json.loads(names[idx + 1])
        names = names[:idx] + names[idx + 2:]

    if "--call" in names:
        idx = names.index("--call")
        names, call = names[:idx] + names[idx + 2:], names[idx + 1]
    return (names or list(load_servers())), call, call_args, force


def describe(exc: BaseException) -> str:
    """Flatten an ExceptionGroup down to the message that actually matters."""
    leaves: list[str] = []
    pending: list[BaseException] = [exc]
    while pending:
        current = pending.pop()
        nested = list(getattr(current, "exceptions", []) or [])
        if nested:
            pending.extend(nested)
            continue
        leaves.append(f"{type(current).__name__}: {current}")
    return " <- ".join(reversed(leaves)) or f"{type(exc).__name__}: {exc}"


def summarise_tools(tools) -> str:
    names = sorted(t.name for t in tools.tools)
    listed = ", ".join(names[:12])
    return f"{len(names)} tools: {listed}" + (" ..." if len(names) > 12 else "")


async def run_call(session: ClientSession, call: str, call_args: dict) -> str:
    result = await session.call_tool(call, call_args or {})
    parts = [getattr(c, "text", None) or repr(getattr(c, "data", "")) for c in result.content]
    body = "\n".join(str(p) for p in parts if p)
    # mcp 2.x renamed the result flag; read it defensively so this harness keeps
    # working across SDK releases.
    failed = getattr(result, "is_error", getattr(result, "isError", False))
    return f"call {call} -> is_error={failed} {body}"


async def probe_stdio(spec: dict, call: str | None, call_args: dict) -> tuple[str, str]:
    env = {**os.environ, **{k: str(v) for k, v in spec.get("env", {}).items()}}
    params = StdioServerParameters(command=spec["command"], args=spec.get("args", []), env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            detail = summarise_tools(await session.list_tools())
            if call:
                detail += " | " + await run_call(session, call, call_args)
            return "PASS", detail


async def probe_http(spec: dict, call: str | None, call_args: dict) -> tuple[str, str]:
    async with streamable_http_client(spec["url"]) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            detail = summarise_tools(await session.list_tools())
            if call:
                detail += " | " + await run_call(session, call, call_args)
            return "PASS", detail


async def main(argv: list[str]) -> int:
    servers = load_servers()
    wanted, call, call_args, force = parse_args(argv)

    unknown = [n for n in wanted if n not in servers]
    if unknown:
        print(f"unknown server(s) in {MCP_CONFIG.name}: {', '.join(unknown)}")
        return 2

    failures = 0
    for index, name in enumerate(wanted):
        spec = servers[name]
        exe = REQUIRES_HOST_APP.get(name)
        if exe and not force and not host_app_running(exe):
            print(f"{name:10} DEFERRED  host app {exe} is not running")
            continue

        transport = "http" if "url" in spec else "stdio"
        this_call = call if call and index == 0 else None
        probe = probe_http if transport == "http" else probe_stdio
        try:
            status, detail = await asyncio.wait_for(probe(spec, this_call, call_args), timeout=300)
        except Exception as exc:  # noqa: BLE001 - report the failure, do not crash the harness
            status, detail = "FAIL", describe(exc)
        if status != "PASS":
            failures += 1
        print(f"{name:10} {status:9} {transport:5} {detail}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))