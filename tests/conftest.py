# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fixtures that run each client test against both clients.

``kind`` is ``"async"`` or ``"sync"``; ``make_client`` builds that client
over an ``httpx.MockTransport``, and ``call`` awaits a result only when
it is awaitable, so one test body exercises both. Waits between retries
are recorded instead of slept.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest

from crypto_service import AsyncClient, Client
from crypto_service._async import _base as async_base
from crypto_service._sync import _base as sync_base

Handler = Callable[[httpx.Request], httpx.Response]
BASE_URL = "http://crypto.test"
API_KEY = "synthetic-api-key"


async def call(result: Any) -> Any:
    """The value of a client call, from either client."""
    return await result if inspect.isawaitable(result) else result


@pytest.fixture(params=["async", "sync"])
def kind(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Waits the clients asked for, instead of sleeping."""
    waited: list[float] = []

    async def fake_async_sleep(seconds: float) -> None:
        waited.append(seconds)

    monkeypatch.setattr(async_base, "_sleep", fake_async_sleep)
    monkeypatch.setattr(sync_base, "_sleep", waited.append)
    return waited


@pytest.fixture
async def make_client(kind: str, sleeps: list[float]) -> AsyncIterator[Callable[..., Any]]:
    """Build the client under test over a mock transport."""
    made: list[Any] = []

    def factory(handler: Handler, **options: Any) -> Any:
        options.setdefault("api_key", API_KEY)
        transport = httpx.MockTransport(handler)
        client = (AsyncClient if kind == "async" else Client)(
            BASE_URL, transport=transport, **options
        )
        made.append(client)
        return client

    yield factory
    for client in made:
        await call(client.aclose() if kind == "async" else client.close())


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Count the conformance vectors that ran, when any did."""
    from .test_conformance import RESULTS

    if not RESULTS:
        return
    passed = sum(len(r.passed) for r in RESULTS)
    total = passed + sum(len(r.failed) for r in RESULTS)
    terminalreporter.write_line(f"conformance: {passed}/{total} vectors passed")
    for result in RESULTS:
        for failure in result.failed:
            terminalreporter.write_line(f"  {result.name}: {failure}")
