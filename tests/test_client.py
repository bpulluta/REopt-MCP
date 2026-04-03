import asyncio
from unittest.mock import AsyncMock

import httpx

from reopt_mcp import client


class _MockResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://example.test")
            response = httpx.Response(self.status_code, request=request, text="error")
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class _MockAsyncClient:
    def __init__(self, response: _MockResponse):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return self._response

    async def get(self, *args, **kwargs):
        return self._response


def test_truncate_large_arrays_truncates_numeric_8760_series() -> None:
    values = [1.0] * 8760
    result = client.truncate_large_arrays({"series": values})

    assert result["series"]["_truncated"] is True
    assert result["series"]["_length"] == 8760
    assert result["series"]["_sum"] == 8760.0


def test_submit_job_returns_run_uuid(monkeypatch) -> None:
    response = _MockResponse({"run_uuid": "run-1"})

    def fake_async_client(*args, **kwargs):
        return _MockAsyncClient(response)

    monkeypatch.setattr(client.httpx, "AsyncClient", fake_async_client)

    run_uuid = asyncio.run(client.submit_job({"Site": {}}))
    assert run_uuid == "run-1"


def test_get_job_data_returns_payload(monkeypatch) -> None:
    payload = {"status": "optimal", "outputs": {}}

    def fake_async_client(*args, **kwargs):
        return _MockAsyncClient(_MockResponse(payload))

    monkeypatch.setattr(client.httpx, "AsyncClient", fake_async_client)

    result = asyncio.run(client.get_job_data("run-1"))
    assert result["status"] == "optimal"


def test_poll_until_complete_returns_complete(monkeypatch) -> None:
    monkeypatch.setattr(
        client,
        "get_job_data_truncated",
        AsyncMock(
            side_effect=[
                {"status": "Optimizing..."},
                {"status": "optimal", "outputs": {}},
            ]
        ),
    )
    monkeypatch.setattr(client.asyncio, "sleep", AsyncMock(return_value=None))

    result = asyncio.run(client.poll_until_complete("run-2", max_wait_seconds=10))

    assert result["status"] == "complete"
    assert result["job_status"] == "optimal"
    assert result["poll_count"] >= 2


def test_poll_until_complete_returns_error_on_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        client, "get_job_data_truncated", AsyncMock(side_effect=RuntimeError("boom"))
    )

    result = asyncio.run(client.poll_until_complete("run-3", max_wait_seconds=10))

    assert result["status"] == "error"
    assert "boom" in result["error"]
