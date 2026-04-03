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
from reopt_mcp.instructions import DEFAULT_INSTRUCTIONS
from reopt_mcp.summaries import (
    build_submit_summary,
    format_financial_summary,
    format_results_summary,
    format_system_summary,
)
from reopt_mcp.validation import guidance_for_errors, validate_scenario

app = Server("reopt-mcp")

READ_ONLY_TOOL_HINTS = types.ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

MUTATING_TOOL_HINTS = types.ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)


def _invalid_request(message: str, next_step: str) -> list[types.TextContent]:
    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "invalid_request",
                    "submission_status": "not_submitted",
                    "error": message,
                    "next_step": next_step,
                },
                indent=2,
            ),
        )
    ]


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="submitAndWait",
            description=(
                "<use_case>Submit REopt optimization and wait for results. PRIMARY tool for running optimizations.</use_case>"
                "<behavior>Builds scenario from user-provided information, submits to NREL API, polls automatically (30-120s), returns results.</behavior>"
                "<critical_validation>MUST have ALL of these BEFORE calling this tool:\n"
                "1. EXACT latitude/longitude (not city name - look up coordinates first)\n"
                "2. EXACT annual_kwh from user (NEVER estimate or make up - ASK if missing)\n"
                "3. VALID doe_reference_name from approved list (NEVER guess - ASK user for building type)\n"
                "4. CORRECT utility rate - Ask for blended rates directly:\n"
                "   a) blended_annual_energy_rate ($/kWh)\n"
                "   b) blended_annual_demand_rate ($/kW, use 0 if none)\n"
                "   Do not block on URDB lookup in the current workflow.\n"
                "5. Technologies: ONLY {} for what user explicitly mentioned (solar=PV, battery=ElectricStorage)\n\n"
                "FORBIDDEN: address field (invalid), made-up annual_kwh, guessed tariff values, unrequested technologies, assumed constraints.\n\n"
                "IF MISSING ANY INFO: STOP and ASK user. Do NOT proceed with assumptions.</critical_validation>"
                "<workflow>When user mentions location but missing details: (1) Ask for building type, (2) Ask for annual kWh, (3) Ask for blended rates ($/kWh and $/kW), (4) Look up coordinates, (5) THEN call submitAndWait with exact values.</workflow>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "REopt scenario with Site, ElectricLoad, ElectricTariff plus technology objects based on user intent (PV, ElectricStorage, etc.). If omitted, tool returns guidance and does not submit.",
                    },
                    "max_wait_seconds": {
                        "type": "integer",
                        "description": "Maximum wait time (default 300s)",
                        "default": 300,
                    },
                },
            },
            annotations=MUTATING_TOOL_HINTS,
        ),
        types.Tool(
            name="getResultsSummary",
            description=(
                "<use_case>Get a concise, user-friendly summary of optimization results. Perfect for presenting recommendations.</use_case>"
                "<aliases>Also known as: summarize results, show recommendations, what did the optimization find</aliases>"
                "<behavior>Returns key metrics in markdown format: system sizes (PV kW, battery kW/kWh), "
                "financial analysis (NPV, payback, IRR), and utility bill savings.</behavior>"
                "<important_notes>This is the RECOMMENDED tool for presenting results to users. "
                "Much more token-efficient than getJobResults.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
            annotations=READ_ONLY_TOOL_HINTS,
        ),
        types.Tool(
            name="getFinancialSummary",
            description=(
                "<use_case>Get detailed financial analysis for investment decision-making.</use_case>"
                "<behavior>Returns comprehensive financial metrics in markdown table format: NPV, LCC, payback period, "
                "IRR, initial capital costs, O&M costs, and incentives.</behavior>"
                "<important_notes>Use when user asks specifically about economics, ROI, payback, or financial viability.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
            annotations=READ_ONLY_TOOL_HINTS,
        ),
        types.Tool(
            name="getSystemSummary",
            description=(
                "<use_case>Get detailed technical specifications for recommended systems.</use_case>"
                "<behavior>Returns technology-specific metrics in markdown tables: system capacities, "
                "energy production, capacity factors, O&M costs for each technology (PV, battery, etc.).</behavior>"
                "<important_notes>Use when user asks about technical details, system specifications, or performance characteristics.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "run_uuid": {
                        "type": "string",
                        "description": "The UUID of the completed optimization job",
                    }
                },
                "required": ["run_uuid"],
            },
            annotations=READ_ONLY_TOOL_HINTS,
        ),
        types.Tool(
            name="validateScenario",
            description=(
                "<use_case>Check if a scenario has all required information before submission.</use_case>"
                "<behavior>Validates scenario structure and returns detailed errors for any missing/invalid fields. "
                "Use this BEFORE calling submitAndWait to catch issues early.</behavior>"
                "<important_notes>This helps identify what information is still needed from the user. "
                "Returns specific validation errors that should be addressed by asking the user.</important_notes>"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "object",
                        "description": "The scenario object to validate",
                    }
                },
                "required": ["scenario"],
            },
            annotations=READ_ONLY_TOOL_HINTS,
        ),
        types.Tool(
            name="getMinimalScenario",
            description=(
                "<use_case>Show the 3 required inputs and how to add technologies.</use_case>"
                "<behavior>Returns base structure (Site, ElectricLoad, ElectricTariff) and explains "
                "how to add technology objects like PV: {}, ElectricStorage: {}, etc.</behavior>"
                "<important_notes>Use when user asks 'how to structure' or 'what's required'. "
                "Teaches that empty {} enables technology evaluation.</important_notes>"
            ),
            inputSchema={"type": "object", "properties": {}},
            annotations=READ_ONLY_TOOL_HINTS,
        ),
        types.Tool(
            name="getExampleScenario",
            description=(
                "<use_case>Show complete working examples for common scenarios.</use_case>"
                "<behavior>Returns 3 examples: solar only, solar+battery, and with constraints.</behavior>"
                "<important_notes>Use when user asks for examples or wants to see different configurations.</important_notes>"
            ),
            inputSchema={"type": "object", "properties": {}},
            annotations=READ_ONLY_TOOL_HINTS,
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    args = arguments if isinstance(arguments, dict) else {}

    if name == "submitAndWait":
        scenario = args.get("scenario")
        max_wait_seconds = args.get("max_wait_seconds", 300)
        if not isinstance(scenario, dict):
            return _invalid_request(
                "'scenario' is required and must be an object.",
                "Call getMinimalScenario for a template, gather missing user inputs, then call submitAndWait with a complete scenario.",
            )
        if not isinstance(max_wait_seconds, int) or max_wait_seconds <= 0:
            return _invalid_request(
                "'max_wait_seconds' must be a positive integer.",
                "Use a positive integer such as 300.",
            )
        return await submit_and_wait(
            scenario,
            max_wait_seconds,
        )
    if name == "getResultsSummary":
        run_uuid = args.get("run_uuid")
        if not _is_nonempty_string(run_uuid):
            return _invalid_request(
                "'run_uuid' is required and must be a non-empty string.",
                "Call submitAndWait first, then pass the returned run_uuid.",
            )
        return await get_results_summary(run_uuid)
    if name == "getFinancialSummary":
        run_uuid = args.get("run_uuid")
        if not _is_nonempty_string(run_uuid):
            return _invalid_request(
                "'run_uuid' is required and must be a non-empty string.",
                "Call submitAndWait first, then pass the returned run_uuid.",
            )
        return await get_financial_summary(run_uuid)
    if name == "getSystemSummary":
        run_uuid = args.get("run_uuid")
        if not _is_nonempty_string(run_uuid):
            return _invalid_request(
                "'run_uuid' is required and must be a non-empty string.",
                "Call submitAndWait first, then pass the returned run_uuid.",
            )
        return await get_system_summary(run_uuid)
    if name == "validateScenario":
        scenario = args.get("scenario")
        if not isinstance(scenario, dict):
            return _invalid_request(
                "'scenario' is required and must be an object.",
                "Provide a scenario object to validate.",
            )
        return await validate_scenario_tool(scenario)
    if name == "getMinimalScenario":
        return await get_minimal_scenario()
    if name == "getExampleScenario":
        return await get_example_scenario()
    return [
        types.TextContent(
            type="text",
            text=(
                f"Unknown tool: {name}. "
                "Use one of: submitAndWait, getResultsSummary, getFinancialSummary, "
                "getSystemSummary, validateScenario, getMinimalScenario, getExampleScenario"
            ),
        )
    ]


async def validate_scenario_tool(scenario: dict) -> list[types.TextContent]:
    is_valid, errors = validate_scenario(scenario)

    if is_valid:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "valid",
                        "message": "✓ Scenario is valid and ready for submission",
                        "scenario": scenario,
                    },
                    indent=2,
                ),
            )
        ]

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "invalid",
                    "valid": False,
                    "errors": errors,
                    "guidance": guidance_for_errors(errors),
                    "message": "Scenario needs more information before submission",
                },
                indent=2,
            ),
        )
    ]


async def submit_and_wait(
    scenario: dict, max_wait_seconds: int = 300
) -> list[types.TextContent]:
    try:
        if not isinstance(scenario, dict):
            return _invalid_request(
                "'scenario' is required and must be an object.",
                "Provide a complete scenario object with Site, ElectricLoad, ElectricTariff, and requested technologies.",
            )

        is_valid, errors = validate_scenario(scenario)
        if not is_valid:
            error_msg = (
                "❌ Cannot submit - scenario is missing required information:\n\n"
            )
            for index, err in enumerate(errors, 1):
                error_msg += f"{index}. {err}\n"
            error_msg += "\n⚠️ Please provide the missing information before submitting."
            error_msg += "\n\nUse getMinimalScenario or getExampleScenario to see proper structure."

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "validation_error",
                            "errors": errors,
                            "message": error_msg,
                            "scenario_received": scenario,
                        },
                        indent=2,
                    ),
                )
            ]

        run_uuid = await submit_job(scenario)
        if not _is_nonempty_string(run_uuid):
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "error",
                            "submission_status": "not_submitted",
                            "error": "REopt API did not return a valid run_uuid.",
                            "next_step": "Retry submitAndWait. If this persists, inspect API response/auth configuration.",
                        },
                        indent=2,
                    ),
                )
            ]

        poll_result = await poll_until_complete(run_uuid, max_wait_seconds)

        if poll_result["status"] == "complete":
            outputs = poll_result["result"].get("outputs", {})
            summary = build_submit_summary(
                run_uuid,
                poll_result["elapsed_seconds"],
                poll_result["job_status"],
                outputs,
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "submission_status": "submitted",
                            "run_uuid": run_uuid,
                            "elapsed_seconds": poll_result["elapsed_seconds"],
                            "summary": summary,
                            "outputs": outputs,
                            "messages": poll_result["result"].get("messages", {}),
                        },
                        indent=2,
                    ),
                )
            ]

        return [types.TextContent(type="text", text=json.dumps(poll_result, indent=2))]

    except httpx.HTTPStatusError as error:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "error": f"HTTP {error.response.status_code}",
                        "detail": error.response.text,
                    },
                    indent=2,
                ),
            )
        ]
    except Exception as error:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "error": str(error)}, indent=2),
            )
        ]


async def get_results_summary(run_uuid: str) -> list[types.TextContent]:
    if not _is_nonempty_string(run_uuid):
        return _invalid_request(
            "'run_uuid' is required and must be a non-empty string.",
            "Call submitAndWait first, then pass the returned run_uuid.",
        )

    try:
        result = await get_job_data(run_uuid)
        return [
            types.TextContent(
                type="text", text=format_results_summary(result.get("outputs", {}))
            )
        ]
    except Exception as error:
        return [types.TextContent(type="text", text=f"Error: {str(error)}")]


async def get_financial_summary(run_uuid: str) -> list[types.TextContent]:
    if not _is_nonempty_string(run_uuid):
        return _invalid_request(
            "'run_uuid' is required and must be a non-empty string.",
            "Call submitAndWait first, then pass the returned run_uuid.",
        )

    try:
        result = await get_job_data(run_uuid)
        return [
            types.TextContent(
                type="text", text=format_financial_summary(result.get("outputs", {}))
            )
        ]
    except Exception as error:
        return [types.TextContent(type="text", text=f"Error: {str(error)}")]


async def get_system_summary(run_uuid: str) -> list[types.TextContent]:
    if not _is_nonempty_string(run_uuid):
        return _invalid_request(
            "'run_uuid' is required and must be a non-empty string.",
            "Call submitAndWait first, then pass the returned run_uuid.",
        )

    try:
        result = await get_job_data(run_uuid)
        return [
            types.TextContent(
                type="text", text=format_system_summary(result.get("outputs", {}))
            )
        ]
    except Exception as error:
        return [types.TextContent(type="text", text=f"Error: {str(error)}")]


async def get_minimal_scenario() -> list[types.TextContent]:
    minimal_base = examples.get_base_inputs()

    explanation = """## Minimal REopt Scenario Structure

### The 3 Required Inputs:

```json
{
  "Site": {
    "latitude": 39.7407,
    "longitude": -104.9890
  },
  "ElectricLoad": {
    "doe_reference_name": "MediumOffice",
    "annual_kwh": 500000
  },
  "ElectricTariff": {
                "blended_annual_energy_rate": 0.12,
                "blended_annual_demand_rate": 15.0
  }
}
```

**CRITICAL**: ElectricLoad needs BOTH fields:
- `doe_reference_name`: Provides hourly load pattern/shape
- `annual_kwh`: Scales the pattern to your consumption
- Together they create the 8760-hour load profile

**That's it for the base!** Now add technologies you want to evaluate:

### Adding Technologies to Evaluate:

To evaluate solar PV:
```json
{
  ...(3 required inputs),
  "PV": {}
}
```

To evaluate solar + battery:
```json
{
  ...(3 required inputs),
  "PV": {},
  "ElectricStorage": {}
}
```

To evaluate solar + battery + wind:
```json
{
  ...(3 required inputs),
  "PV": {},
  "ElectricStorage": {},
  "Wind": {}
}
```

### Key Concept:

✅ Empty object `{}` = "Evaluate this technology using default assumptions"
❌ No object = "Don't consider this technology at all"

### Settings Rule (Important):

- On-grid (default): include `ElectricTariff`
- Off-grid: set `"Settings": {"off_grid_flag": true}` and remove `ElectricTariff`

### REopt.jl Key Accuracy:

- Use REopt.jl key names exactly (for example: `blended_annual_energy_rate`, `blended_annual_demand_rate`)
- Avoid alias keys with unit suffixes that are not accepted by REopt.jl

### Available Technologies:

- `"PV": {}` - Solar photovoltaic
- `"ElectricStorage": {}` - Battery storage
- `"Wind": {}` - Wind turbines
- `"Generator": {}` - Backup generator
- `"CHP": {}` - Combined heat & power

### When to Add Constraints:

Only add parameters if you have specific limits:
```json
"PV": {
  "max_kw": 500  // Only if limited by roof space or budget
}
```

Otherwise, use empty `{}` to let REopt find the optimal size!

Types: MediumOffice, RetailStore, Hospital, LargeHotel, Warehouse, School, etc."""

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "base_structure": minimal_base,
                    "description": explanation,
                },
                indent=2,
            ),
        )
    ]


async def get_example_scenario() -> list[types.TextContent]:
    examples_data = {
        "solar_only": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {
                "doe_reference_name": "MediumOffice",
                "annual_kwh": 500000,
            },
            "ElectricTariff": {
                "blended_annual_energy_rate": 0.12,
                "blended_annual_demand_rate": 15.0,
            },
            "PV": {},
        },
        "solar_and_battery": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {
                "doe_reference_name": "MediumOffice",
                "annual_kwh": 800000,
            },
            "ElectricTariff": {
                "blended_annual_energy_rate": 0.12,
                "blended_annual_demand_rate": 15.0,
            },
            "PV": {},
            "ElectricStorage": {},
        },
        "with_constraints": {
            "Site": {"latitude": 39.7407, "longitude": -104.9890},
            "ElectricLoad": {
                "doe_reference_name": "LargeOffice",
                "annual_kwh": 1000000,
            },
            "ElectricTariff": {
                "blended_annual_energy_rate": 0.12,
                "blended_annual_demand_rate": 15.0,
            },
            "PV": {"max_kw": 500},
            "ElectricStorage": {"max_kw": 250, "max_kwh": 1000},
        },
    }

    explanation = """## REopt Scenario Examples

### Example 1: Solar Only
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "MediumOffice", "annual_kwh": 500000},
    "ElectricTariff": {
        "blended_annual_energy_rate": 0.12,
        "blended_annual_demand_rate": 15.0
    },
  "PV": {}
}
```
Evaluates solar PV with no constraints - REopt determines optimal size.

### Example 2: Solar + Battery
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "RetailStore", "annual_kwh": 800000},
    "ElectricTariff": {
        "blended_annual_energy_rate": 0.12,
        "blended_annual_demand_rate": 15.0
    },
  "PV": {},
  "ElectricStorage": {}
}
```
Evaluates solar + battery with no constraints.

### Example 3: With Space/Budget Constraints
```json
{
  "Site": {"latitude": 39.7407, "longitude": -104.9890},
  "ElectricLoad": {"doe_reference_name": "LargeOffice", "annual_kwh": 1000000},
    "ElectricTariff": {
        "blended_annual_energy_rate": 0.12,
        "blended_annual_demand_rate": 15.0
    },
  "PV": {"max_kw": 500},
  "ElectricStorage": {"max_kw": 250, "max_kwh": 1000}
}
```
Only use constraints when you have actual limitations!

### Building Your Scenario:

1. Start with 3 required inputs
2. Add empty `{}` for each technology you want to evaluate
3. Only add constraints if you have specific limits
4. Submit and let REopt optimize!"""

    return [
        types.TextContent(
            type="text",
            text=json.dumps(
                {
                    "status": "success",
                    "examples": examples_data,
                    "description": explanation,
                },
                indent=2,
            ),
        )
    ]


async def main() -> None:
    warn_if_unconfigured()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="reopt-mcp",
            server_version="0.2.0",
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
