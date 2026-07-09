import asyncio
import json
from unittest.mock import patch

from reopt_mcp import mock, simulate, tools


def test_list_tools_exposes_four_tools() -> None:
    listed = asyncio.run(tools.list_tools())
    names = {tool.name for tool in listed}

    assert names == set(tools.TOOL_NAMES)
    assert all(tool.annotations is not None for tool in listed)


def test_call_tool_handles_none_arguments_for_noarg_tool() -> None:
    result = asyncio.run(tools.call_tool("getScenarioHelp", None))

    payload = json.loads(result[0].text)
    assert payload["status"] == "success"
    assert payload["name"] == "minimal"
    assert "scenario" in payload


def test_get_scenario_help_returns_named_example() -> None:
    result = asyncio.run(tools.call_tool("getScenarioHelp", {"name": "solar"}))

    payload = json.loads(result[0].text)
    assert payload["status"] == "success"
    assert payload["name"] == "solar"
    assert "PV" in payload["scenario"]


def test_unknown_tool_message_lists_supported_tools() -> None:
    result = asyncio.run(tools.call_tool("doesNotExist", None))

    assert "Unknown tool" in result[0].text
    assert "submitAndWait" in result[0].text


def test_get_summary_requires_run_uuid() -> None:
    result = asyncio.run(tools.call_tool("getSummary", {}))

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert "run_uuid" in payload["error"]


def test_get_summary_rejects_unknown_kind() -> None:
    result = asyncio.run(
        tools.call_tool("getSummary", {"run_uuid": "abc", "kind": "nope"})
    )

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert "kind" in payload["error"]


def test_submit_and_wait_requires_scenario_object() -> None:
    result = asyncio.run(tools.call_tool("submitAndWait", {}))

    payload = json.loads(result[0].text)
    assert payload["status"] == "invalid_request"
    assert payload["submission_status"] == "not_submitted"
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


def test_submit_and_wait_previews_without_confirm() -> None:
    result = asyncio.run(
        tools.call_tool(
            "submitAndWait",
            {"scenario": mock.load_fixture("solar_scenario.json")},
        )
    )

    payload = json.loads(result[0].text)
    assert payload["status"] == "preview_required"
    assert payload["submission_status"] == "not_submitted"
    assert "PV" in payload["technologies"]
    assert "confirm=true" in payload["next_step"]


def test_submit_and_wait_mock_flow() -> None:
    with (
        patch.object(tools, "submit_job", mock.mock_submit_job),
        patch.object(tools, "poll_until_complete", mock.mock_poll_until_complete),
    ):
        result = asyncio.run(
            tools.call_tool(
                "submitAndWait",
                {
                    "scenario": mock.load_fixture("solar_scenario.json"),
                    "confirm": True,
                    "max_wait_seconds": 30,
                },
            )
        )

    payload = json.loads(result[0].text)
    assert payload["status"] == "success"
    assert payload["run_uuid"] == mock.MOCK_RUN_UUID
    assert payload["outputs"]["PV"]["size_kw"] == 120


def test_get_summary_error_returns_structured_contract() -> None:
    async def boom(_run_uuid):
        raise RuntimeError("network down")

    with patch.object(tools, "get_job_data", boom):
        result = asyncio.run(
            tools.call_tool("getSummary", {"run_uuid": "abc", "kind": "results"})
        )

    payload = json.loads(result[0].text)
    assert payload["status"] == "error"
    assert "abc" in payload["error"]
    assert "next_step" in payload


def test_get_summary_renders_wind_generator_via_mock() -> None:
    async def fake_get_job_data(_run_uuid):
        return mock.load_fixture("wind_generator_result.json")

    with patch.object(tools, "get_job_data", fake_get_job_data):
        result = asyncio.run(
            tools.call_tool("getSummary", {"run_uuid": "abc", "kind": "all"})
        )

    text = result[0].text
    assert "Wind" in text
    assert "Backup Generator" in text


def test_simulate_call_validate_fixture(capsys) -> None:
    code = simulate.main(
        [
            "call",
            "validateScenario",
            "--input",
            "tests/fixtures/solar_scenario.json",
        ]
    )

    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert code == 0
    assert payload["status"] == "valid"


def test_simulate_call_submit_preview(capsys) -> None:
    code = simulate.main(
        [
            "call",
            "submitAndWait",
            "--input",
            "tests/fixtures/solar_scenario.json",
            "--mock",
        ]
    )

    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert code == 0
    assert payload["status"] == "preview_required"


def test_simulate_call_submit_mock(capsys) -> None:
    code = simulate.main(
        [
            "call",
            "submitAndWait",
            "--input",
            "tests/fixtures/solar_scenario.json",
            "--args",
            '{"confirm": true}',
            "--mock",
        ]
    )

    captured = capsys.readouterr().out
    payload = json.loads(captured)

    assert code == 0
    assert payload["status"] == "success"
    assert payload["run_uuid"] == mock.MOCK_RUN_UUID
