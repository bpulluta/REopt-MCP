import asyncio
import os

import pytest

from reopt_mcp.client import get_job_data, submit_job
from reopt_mcp.examples import get_solar_scenario


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("NREL_API_KEY") or os.getenv("RUN_INTEGRATION_TESTS", "0") != "1",
    reason="Set NREL_API_KEY and RUN_INTEGRATION_TESTS=1 to run integration tests.",
)
def test_submit_and_fetch_job_results() -> None:
    scenario = get_solar_scenario()
    run_uuid = asyncio.run(submit_job(scenario))

    assert run_uuid

    result = asyncio.run(get_job_data(run_uuid))
    assert "status" in result
