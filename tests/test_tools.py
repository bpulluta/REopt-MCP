import asyncio
import json

from reopt_mcp import tools


def test_list_tools_exposes_annotations() -> None:
    listed_tools = asyncio.run(tools.list_tools())

    assert listed_tools
    assert all(t.annotations is not None for t in listed_tools)


def test_call_tool_handles_none_arguments_for_noarg_tool() -> None:
    result = asyncio.run(tools.call_tool("getExampleScenario", None))

    payload = json.loads(result[0].text)
    assert payload["status"] == "success"
    assert "examples" in payload


def test_unknown_tool_message_lists_supported_tools() -> None:
    result = asyncio.run(tools.call_tool("doesNotExist", None))

    assert "Unknown tool" in result[0].text
    assert "submitAndWait" in result[0].text


def test_get_results_summary_requires_run_uuid() -> None:
    result = asyncio.run(tools.call_tool("getResultsSummary", {}))

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert "run_uuid" in payload["error"]


def test_submit_and_wait_requires_scenario_object() -> None:
    result = asyncio.run(tools.call_tool("submitAndWait", {}))

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert "scenario" in payload["error"]


def test_submit_and_wait_rejects_invalid_max_wait_seconds() -> None:
    result = asyncio.run(
        tools.call_tool(
            "submitAndWait",
            {
                "scenario": {
                    "Site": {"latitude": 39.7407, "longitude": -104.9890},
                    "ElectricLoad": {
                        "doe_reference_name": "MediumOffice",
                        "annual_kwh": 500000,
                    },
                    "ElectricTariff": {
                        "blended_annual_energy_rate": 0.12,
                        "blended_annual_demand_rate": 15.0,
                    },
                },
                "max_wait_seconds": 0,
            },
        )
    )

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert "max_wait_seconds" in payload["error"]
