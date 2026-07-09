"""Mock REopt API responses for local simulation."""

from pathlib import Path

MOCK_RUN_UUID = "mock-run-001"
_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    import json

    return json.loads((_FIXTURES / name).read_text())


async def mock_submit_job(_scenario: dict) -> str:
    return MOCK_RUN_UUID


async def mock_get_job_data(_run_uuid: str) -> dict:
    return load_fixture("optimal_result.json")


async def mock_poll_until_complete(run_uuid: str, max_wait_seconds: int = 300) -> dict:
    result = await mock_get_job_data(run_uuid)
    return {
        "status": "complete",
        "job_status": result.get("status", "optimal"),
        "result": result,
        "run_uuid": run_uuid,
        "elapsed_seconds": 3,
        "poll_count": 1,
    }
