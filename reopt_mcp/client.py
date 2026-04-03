"""REopt API client and polling helpers."""

import asyncio
from typing import Any

import httpx

from reopt_mcp.config import NREL_API_KEY, REOPT_API_BASE_URL


def truncate_large_arrays(data: Any) -> Any:
    """Recursively truncate 8760+ timeseries arrays to summary statistics."""
    if isinstance(data, dict):
        return {k: truncate_large_arrays(v) for k, v in data.items()}
    if isinstance(data, list):
        if len(data) >= 8760:
            is_numeric = all(isinstance(x, (int, float)) for x in data)
            if is_numeric:
                return {
                    "_truncated": True,
                    "_type": "timeseries",
                    "_length": len(data),
                    "_sum": round(sum(data), 2),
                    "_mean": round(sum(data) / len(data), 4),
                    "_min": round(min(data), 4),
                    "_max": round(max(data), 4),
                }
        return [truncate_large_arrays(item) for item in data]
    return data


async def submit_job(scenario: dict) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{REOPT_API_BASE_URL}/job",
            json=scenario,
            params={"api_key": NREL_API_KEY},
        )
        response.raise_for_status()
        return response.json().get("run_uuid")


async def get_job_data(run_uuid: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{REOPT_API_BASE_URL}/job/{run_uuid}/results",
            params={"api_key": NREL_API_KEY},
        )
        response.raise_for_status()
        return response.json()


async def get_job_data_truncated(run_uuid: str) -> dict:
    result = await get_job_data(run_uuid)
    return truncate_large_arrays(result)


async def poll_until_complete(run_uuid: str, max_wait_seconds: int = 300) -> dict:
    start_time = asyncio.get_event_loop().time()
    poll_interval = 3
    max_interval = 15
    poll_count = 0

    while True:
        poll_count += 1
        elapsed = asyncio.get_event_loop().time() - start_time

        if elapsed > max_wait_seconds:
            return {
                "status": "timeout",
                "message": f"Job did not complete within {max_wait_seconds} seconds (polled {poll_count} times)",
                "run_uuid": run_uuid,
                "elapsed_seconds": int(elapsed),
            }

        try:
            result = await get_job_data_truncated(run_uuid)
            job_status = result.get("status", "Unknown")

            if job_status in ["optimal", "not optimal"]:
                return {
                    "status": "complete",
                    "job_status": job_status,
                    "result": result,
                    "run_uuid": run_uuid,
                    "elapsed_seconds": int(elapsed),
                    "poll_count": poll_count,
                }

            await asyncio.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.3, max_interval)

        except Exception as error:
            return {
                "status": "error",
                "error": str(error),
                "run_uuid": run_uuid,
                "elapsed_seconds": int(elapsed),
                "poll_count": poll_count,
            }
