"""MCP tool definitions and handlers."""

import asyncio
import json
from typing import Any

import httpx
import mcp.types as types
import mcp.server.stdio
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions

from reopt_mcp import examples
from reopt_mcp.client import get_job_data, poll_until_complete, submit_job
from reopt_mcp.config import warn_if_unconfigured
from reopt_mcp.constants import KNOWN_TECHNOLOGIES, VALID_DOE_REFERENCE_NAMES
from reopt_mcp.instructions import DEFAULT_INSTRUCTIONS
from reopt_mcp.summaries import (
    build_submit_summary,
    format_financial_summary,
    format_results_summary,
    format_system_summary,
)
from reopt_mcp.validation import (
    guidance_for_errors,
    scenario_warnings,
    validate_scenario,
)

TOOL_NAMES = (
    "submitAndWait",
    "validateScenario",
    "getScenarioHelp",
    "getSummary",
)

app = Server("reopt-mcp")

READ_ONLY = types.ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

MUTATING = types.ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

SUMMARY_FORMATTERS = {
    "results": format_results_summary,
    "financial": format_financial_summary,
    "system": format_system_summary,
}


def _text(payload: Any) -> list[types.TextContent]:
    if isinstance(payload, str):
        text = payload
    else:
        text = json.dumps(payload, indent=2)
    return [types.TextContent(type="text", text=text)]


def _error(
    message: str,
    *,
    status: str = "invalid_request",
    next_step: str | None = None,
    **extra: Any,
) -> list[types.TextContent]:
    body: dict[str, Any] = {"status": status, "error": message}
    if next_step:
        body["next_step"] = next_step
    body.update(extra)
    return _text(body)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="submitAndWait",
            description=(
                "Validate and (once confirmed) submit a REopt scenario, poll until "
                "complete, and return results. Requires Site (lat/lon), ElectricLoad "
                "(doe_reference_name + annual_kwh), ElectricTariff (blended rates or "
                "urdb_label), and empty {} for each requested technology (PV, "
                "ElectricStorage, Wind, Generator). TWO-STEP GATE: call first WITHOUT "
                "confirm to get a preview of the exact scenario for the user to review; "
                "only after the user approves, call again with confirm=true to actually "
                "submit. Ask the user for missing values before calling."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "Complete REopt scenario JSON.",
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": (
                            "Must be true to actually submit. When false/omitted, the "
                            "tool validates and returns a preview WITHOUT submitting so "
                            "the user can confirm inputs first."
                        ),
                        "default": False,
                    },
                    "max_wait_seconds": {
                        "type": "integer",
                        "description": "Max poll time in seconds (default 300).",
                        "default": 300,
                    },
                },
            },
            annotations=MUTATING,
        ),
        types.Tool(
            name="validateScenario",
            description=(
                "Check a scenario for missing or invalid fields before submission. "
                "Returns errors and guidance on what to ask the user."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {"type": "object"},
                },
                "required": ["scenario"],
            },
            annotations=READ_ONLY,
        ),
        types.Tool(
            name="getScenarioHelp",
            description=(
                "Show scenario structure and examples. "
                "Use name='minimal' for required fields, 'all' for every example, "
                "or a key like 'solar' or 'solar_battery'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "minimal | all | solar | solar_battery | pv_and_storage | resilience | wind",
                    }
                },
            },
            annotations=READ_ONLY,
        ),
        types.Tool(
            name="getSummary",
            description=(
                "Format optimization results as markdown. "
                "kind: results (default), financial, system, or all."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "Run UUID from submitAndWait.",
                    },
                    "kind": {
                        "type": "string",
                        "enum": ["results", "financial", "system", "all"],
                        "default": "results",
                    },
                },
                "required": ["run_uuid"],
            },
            annotations=READ_ONLY,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    args = arguments if isinstance(arguments, dict) else {}

    if name == "submitAndWait":
        return await _submit_and_wait(args)
    if name == "validateScenario":
        return await _validate_scenario_tool(args.get("scenario"))
    if name == "getScenarioHelp":
        return await _get_scenario_help(args.get("name", "minimal"))
    if name == "getSummary":
        return await _get_summary(args.get("run_uuid"), args.get("kind", "results"))
    return _text(f"Unknown tool: {name}. Available: {', '.join(TOOL_NAMES)}")


async def _validate_scenario_tool(scenario: Any) -> list[types.TextContent]:
    if not isinstance(scenario, dict):
        return _error(
            "'scenario' is required and must be an object.",
            next_step="Provide a scenario object to validate.",
        )

    is_valid, errors = validate_scenario(scenario)
    if is_valid:
        return _text(
            {
                "status": "valid",
                "message": "Scenario is valid and ready for submission.",
                "scenario": scenario,
            }
        )

    return _text(
        {
            "status": "invalid",
            "errors": errors,
            "guidance": guidance_for_errors(errors),
            "message": "Scenario needs more information before submission.",
        }
    )


def _requested_technologies(scenario: dict) -> list[str]:
    return [tech for tech in sorted(KNOWN_TECHNOLOGIES) if tech in scenario]


async def _submit_and_wait(args: dict) -> list[types.TextContent]:
    scenario = args.get("scenario")
    max_wait_seconds = args.get("max_wait_seconds", 300)
    confirm = args.get("confirm", False)

    if not isinstance(scenario, dict):
        return _error(
            "'scenario' is required and must be an object.",
            submission_status="not_submitted",
            next_step="Call getScenarioHelp, gather user inputs, then retry.",
        )
    if not isinstance(max_wait_seconds, int) or max_wait_seconds <= 0:
        return _error(
            "'max_wait_seconds' must be a positive integer.",
            next_step="Use a positive integer such as 300.",
        )

    is_valid, errors = validate_scenario(scenario)
    if not is_valid:
        return _text(
            {
                "status": "validation_error",
                "submission_status": "not_submitted",
                "errors": errors,
                "guidance": guidance_for_errors(errors),
                "scenario_received": scenario,
            }
        )

    warnings = scenario_warnings(scenario)

    # Human-in-the-loop gate: never submit until the user has confirmed the
    # exact inputs. Without confirm=true we return a preview and stop here.
    if confirm is not True:
        return _text(
            {
                "status": "preview_required",
                "submission_status": "not_submitted",
                "scenario": scenario,
                "technologies": _requested_technologies(scenario),
                "warnings": warnings,
                "next_step": (
                    "Show this scenario to the user and confirm the inputs are "
                    "correct. Once approved, call submitAndWait again with the same "
                    "scenario and confirm=true to run the optimization."
                ),
            }
        )

    try:
        run_uuid = await submit_job(scenario)
        if not _is_nonempty_string(run_uuid):
            return _error(
                "REopt API did not return a valid run_uuid.",
                status="error",
                submission_status="not_submitted",
                next_step="Check NLR_API_KEY and retry.",
            )

        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)
        if poll_result["status"] != "complete":
            return _text(poll_result)

        outputs = poll_result["result"].get("outputs", {})
        return _text(
            {
                "status": "success",
                "submission_status": "submitted",
                "run_uuid": run_uuid,
                "elapsed_seconds": poll_result["elapsed_seconds"],
                "warnings": warnings,
                "summary": build_submit_summary(
                    run_uuid,
                    poll_result["elapsed_seconds"],
                    poll_result["job_status"],
                    outputs,
                ),
                "outputs": outputs,
                "messages": poll_result["result"].get("messages", {}),
            }
        )
    except httpx.HTTPStatusError as error:
        return _error(
            f"HTTP {error.response.status_code}",
            status="error",
            detail=error.response.text,
        )
    except Exception as error:
        return _error(str(error), status="error")


async def _get_scenario_help(name: str) -> list[types.TextContent]:
    all_examples = examples.get_all_examples()
    valid_names = ["minimal", "all", *sorted(all_examples.keys())]

    if name == "minimal":
        return _text(
            {
                "status": "success",
                "name": "minimal",
                "scenario": examples.get_base_inputs(),
                "building_types": sorted(VALID_DOE_REFERENCE_NAMES),
                "supported_technologies": sorted(KNOWN_TECHNOLOGIES),
                "notes": [
                    "ElectricLoad needs both doe_reference_name and annual_kwh.",
                    "Add empty {} for each technology to evaluate (PV, ElectricStorage, Wind, Generator).",
                    "On-grid scenarios require ElectricTariff with blended rates or urdb_label.",
                    "Off-grid: set Settings.off_grid_flag=true and omit ElectricTariff.",
                    "submitAndWait previews first; call again with confirm=true after the user approves.",
                ],
            }
        )

    if name == "all":
        return _text(
            {
                "status": "success",
                "examples": {
                    key: {
                        "name": item["name"],
                        "description": item["description"],
                        "scenario": item["scenario"],
                    }
                    for key, item in all_examples.items()
                },
            }
        )

    if name in all_examples:
        item = all_examples[name]
        return _text(
            {
                "status": "success",
                "name": name,
                "title": item["name"],
                "description": item["description"],
                "scenario": item["scenario"],
            }
        )

    return _error(
        f"Unknown example '{name}'.",
        next_step=f"Use one of: {', '.join(valid_names)}",
    )


async def _get_summary(run_uuid: Any, kind: str) -> list[types.TextContent]:
    if not _is_nonempty_string(run_uuid):
        return _error(
            "'run_uuid' is required and must be a non-empty string.",
            next_step="Call submitAndWait first, then pass the returned run_uuid.",
        )

    if kind not in SUMMARY_FORMATTERS and kind != "all":
        return _error(
            f"Unknown kind '{kind}'.",
            next_step=f"Use one of: {', '.join([*SUMMARY_FORMATTERS, 'all'])}",
        )

    try:
        result = await get_job_data(run_uuid)
    except httpx.HTTPStatusError as error:
        return _error(
            f"HTTP {error.response.status_code} fetching results for '{run_uuid}'.",
            status="error",
            detail=error.response.text,
            next_step="Verify the run_uuid and NLR_API_KEY, then retry.",
        )
    except Exception as error:
        return _error(
            f"Could not fetch results for '{run_uuid}': {error}",
            status="error",
            next_step="Verify the run_uuid from submitAndWait and retry.",
        )

    outputs = result.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        return _error(
            f"No results available for run '{run_uuid}'.",
            status="error",
            job_status=result.get("status"),
            next_step="The job may still be running or may have failed; check submitAndWait output.",
        )

    if kind == "all":
        sections = [
            format_results_summary(outputs),
            format_financial_summary(outputs),
            format_system_summary(outputs),
        ]
        return [types.TextContent(type="text", text="\n\n---\n\n".join(sections))]

    return [types.TextContent(type="text", text=SUMMARY_FORMATTERS[kind](outputs))]


async def main() -> None:
    warn_if_unconfigured()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="reopt-mcp",
            server_version="0.4.0",
            capabilities=app.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )

        if hasattr(init_options, "instructions"):
            init_options.instructions = DEFAULT_INSTRUCTIONS

        await app.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
