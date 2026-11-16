# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Behaviour only the asynchronous client has: cancellation and attempt scopes."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from crypto_service import AsyncClient, RetryOptions, TransportError

from .conftest import BASE_URL


async def slow(request: httpx.Request) -> httpx.Response:
    await asyncio.sleep(10)
    return httpx.Response(200, json={"data": {}})  # pragma: no cover - never reached


async def test_attempt_timeout_covers_the_whole_attempt() -> None:
    async with AsyncClient(BASE_URL, timeout=0.05, transport=httpx.MockTransport(slow)) as client:
        with pytest.raises(TransportError) as caught:
            await client.hash(algorithm="sha256", data="abc")
    assert caught.value.timed_out
    assert isinstance(caught.value.__cause__, TimeoutError)


async def test_deadline_bounds_retries_of_slow_attempts(sleeps: list[float]) -> None:
    client = AsyncClient(
        BASE_URL,
        timeout=None,
        deadline=0.1,
        retry=RetryOptions(max_retries=5),
        transport=httpx.MockTransport(slow),
    )
    async with client:
        with pytest.raises(TransportError) as caught:
            await client.hash(algorithm="sha256", data="abc")
    assert caught.value.timed_out


async def test_cancellation_propagates() -> None:
    async with AsyncClient(BASE_URL, transport=httpx.MockTransport(slow)) as client:
        task = asyncio.create_task(client.hash(algorithm="sha256", data="abc"))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
