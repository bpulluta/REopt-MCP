"""Run MCP tools locally without an MCP client.

Examples:
  python -m reopt_mcp.simulate list
  python -m reopt_mcp.simulate call validateScenario --input tests/fixtures/solar_scenario.json
  python -m reopt_mcp.simulate call submitAndWait --input tests/fixtures/solar_scenario.json --mock
  python -m reopt_mcp.simulate call getSummary --args '{"run_uuid":"mock-run-001","kind":"all"}' --mock
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from reopt_mcp import mock, tools


def _load_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    path = Path(value)
    if path.exists():
        return json.loads(path.read_text())
    return json.loads(value)


def _apply_mock() -> None:
    tools.submit_job = mock.mock_submit_job
    tools.poll_until_complete = mock.mock_poll_until_complete
    tools.get_job_data = mock.mock_get_job_data


def _looks_like_scenario(data: dict[str, Any]) -> bool:
    return "Site" in data or "ElectricLoad" in data


async def _run_tool(name: str, args: dict[str, Any]) -> list[Any]:
    return await tools.call_tool(name, args)


def _print_result(result: list[Any]) -> None:
    for item in result:
        text = getattr(item, "text", str(item))
        try:
            parsed = json.loads(text)
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print(text)


def cmd_list(_: argparse.Namespace) -> int:
    listed = asyncio.run(tools.list_tools())
    for tool in listed:
        print(f"{tool.name}")
        print(f"  {tool.description}")
        schema = json.dumps(tool.inputSchema, indent=2)
        print(f"  input: {schema}")
        print()
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    if args.mock:
        _apply_mock()

    tool_args: dict[str, Any] = {}
    input_data = _load_json(args.input)
    if input_data:
        if args.tool in {"validateScenario", "submitAndWait"} and _looks_like_scenario(
            input_data
        ):
            tool_args["scenario"] = input_data
        else:
            tool_args.update(input_data)

    # --args carries top-level tool arguments (confirm, max_wait_seconds, run_uuid).
    if args.args:
        tool_args.update(_load_json(args.args))

    if args.tool == "getScenarioHelp" and not tool_args and args.name:
        tool_args = {"name": args.name}

    result = asyncio.run(_run_tool(args.tool, tool_args))
    _print_result(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate REopt MCP tool calls.")
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List available tools and schemas.")
    list_cmd.set_defaults(func=cmd_list)

    call_cmd = sub.add_parser("call", help="Invoke a tool and print the response.")
    call_cmd.add_argument("tool", choices=tools.TOOL_NAMES)
    call_cmd.add_argument(
        "--input",
        "-i",
        help="JSON file path or inline JSON used as tool arguments.",
    )
    call_cmd.add_argument(
        "--args",
        "-a",
        help="Extra JSON merged into tool arguments (file path or inline JSON).",
    )
    call_cmd.add_argument(
        "--name",
        help="Shortcut for getScenarioHelp name (e.g. minimal, solar, all).",
    )
    call_cmd.add_argument(
        "--mock",
        action="store_true",
        help="Use fixture data instead of calling the live REopt API.",
    )
    call_cmd.set_defaults(func=cmd_call)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
