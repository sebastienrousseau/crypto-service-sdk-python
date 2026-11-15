# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every typed method sends the documented request and returns the answer."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from crypto_service import USER_AGENT, AsyncClient, Client

from .conftest import API_KEY, call
from .operations import OPS, PUBLIC, Op

ANSWER = {"value": "synthetic"}


@pytest.mark.parametrize("op", OPS, ids=lambda op: f"{op.name}:{op.path}")
async def test_operation_sends_the_documented_request(
    op: Op, make_client: Callable[..., Any]
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": ANSWER} if op.wrapped else ANSWER)

    client = make_client(handler)
    result = await call(getattr(client, op.name)(**op.kwargs))

    assert result == ANSWER
    (request,) = seen
    assert request.method == op.method
    assert request.url.path == op.path
    assert request.headers["user-agent"] == USER_AGENT
    check_body(op, request)
    check_credentials(op, request)


def check_body(op: Op, request: httpx.Request) -> None:
    if op.body is None:
        assert request.content == b""
        assert "content-type" not in request.headers
        return
    assert json.loads(request.content) == op.body
    assert request.headers["content-type"] == "application/json"


def check_credentials(op: Op, request: httpx.Request) -> None:
    expected = None if op.path in PUBLIC else API_KEY
    assert request.headers.get("x-api-key") == expected


def _public_methods(cls: type) -> set[str]:
    return {name for name in dir(cls) if not name.startswith("_")}


def test_both_clients_have_the_same_methods() -> None:
    expected = _public_methods(AsyncClient) - {"aclose"}
    assert _public_methods(Client) - {"close"} == expected
    for name in expected:
        is_coroutine = inspect.iscoroutinefunction(getattr(AsyncClient, name))
        assert is_coroutine
        assert not inspect.iscoroutinefunction(getattr(Client, name))


def test_every_typed_method_is_exercised() -> None:
    typed = _public_methods(AsyncClient) - {"aclose", "request"}
    assert {op.name for op in OPS} == typed
