# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Retries, timeouts, deadlines, errors and credentials, on both clients."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from typing import Any

import httpx
import pytest

from crypto_service import ApiError, RetryOptions, TransportError, _core

from .conftest import BASE_URL, call

PROBLEM = {
    "type": "urn:crypto-service:problem:key-not-found",
    "title": "Key not found",
    "status": 404,
    "detail": "No key k_x",
    "instance": "/v2/sign",
    "code": "KEY_NOT_FOUND",
}


def ok() -> httpx.Response:
    return httpx.Response(200, json={"data": {"digest": "00"}})


def scripted(*steps: httpx.Response | Exception) -> tuple[Callable[..., Any], list[httpx.Request]]:
    """A handler answering with each step in turn; exceptions are raised."""
    remaining: Iterator[httpx.Response | Exception] = iter(steps)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        step = next(remaining)
        if isinstance(step, Exception):
            raise step
        return step

    return handler, seen


async def hash_abc(client: Any) -> Any:
    return await call(client.hash(algorithm="sha256", data="abc"))


async def test_api_error_carries_the_problem(make_client: Callable[..., Any]) -> None:
    handler, _ = scripted(httpx.Response(404, json=PROBLEM))
    with pytest.raises(ApiError) as caught:
        await call(make_client(handler).sign(key_id="k_x", message="secret message"))
    error = caught.value
    assert error.status == 404
    assert error.code == "KEY_NOT_FOUND"
    assert error.problem.detail == "No key k_x"
    assert error.problem.raw == PROBLEM
    assert "secret message" not in repr(error) + str(error)
    assert "No key" not in repr(error) + str(error)


async def test_non_problem_body_becomes_about_blank(make_client: Callable[..., Any]) -> None:
    handler, _ = scripted(httpx.Response(502, text="<html>bad gateway</html>"))
    with pytest.raises(ApiError) as caught:
        await hash_abc(make_client(handler))
    assert caught.value.problem.type == "about:blank"
    assert caught.value.problem.title == "Bad Gateway"
    assert caught.value.status == 502


async def test_no_retry_by_default(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(503, json={"detail": "busy"}))
    with pytest.raises(ApiError):
        await hash_abc(make_client(handler))
    assert len(seen) == 1


@pytest.mark.parametrize("status", [429, 503, 504])
async def test_transient_statuses_are_retried(
    status: int, make_client: Callable[..., Any], sleeps: list[float]
) -> None:
    handler, seen = scripted(httpx.Response(status), ok())
    client = make_client(handler, retry=RetryOptions(max_retries=2))
    assert await hash_abc(client) == {"digest": "00"}
    assert len(seen) == 2
    assert len(sleeps) == 1
    assert 0 <= sleeps[0] <= 0.2


async def test_retries_stop_at_the_limit(
    make_client: Callable[..., Any], sleeps: list[float]
) -> None:
    handler, seen = scripted(*[httpx.Response(503)] * 3)
    client = make_client(handler, retry=RetryOptions(max_retries=2, initial_delay=1, max_delay=5))
    with pytest.raises(ApiError):
        await hash_abc(client)
    assert len(seen) == 3
    assert sleeps[0] <= 1
    assert sleeps[1] <= 2


async def test_retry_after_is_honoured(
    make_client: Callable[..., Any], sleeps: list[float]
) -> None:
    handler, _ = scripted(httpx.Response(429, headers={"retry-after": "1"}), ok())
    await hash_abc(make_client(handler, retry=RetryOptions(max_retries=1)))
    assert sleeps == [1.0]


async def test_long_retry_after_ends_the_retries(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(429, headers={"retry-after": "60"}))
    with pytest.raises(ApiError) as caught:
        await hash_abc(make_client(handler, retry=RetryOptions(max_retries=3)))
    assert caught.value.status == 429
    assert len(seen) == 1


async def test_client_errors_are_not_retried(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(400, json={"detail": "bad"}))
    with pytest.raises(ApiError):
        await hash_abc(make_client(handler, retry=RetryOptions(max_retries=3)))
    assert len(seen) == 1


async def test_stateful_routes_are_not_retried_after_504(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(504))
    client = make_client(handler, retry=RetryOptions(max_retries=3))
    with pytest.raises(ApiError):
        await call(client.generate_key_pair())
    assert len(seen) == 1


async def test_stateful_routes_are_retried_after_503(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(503), httpx.Response(200, json={"data": {"k": 1}}))
    client = make_client(handler, retry=RetryOptions(max_retries=1))
    assert await call(client.kms_create_key()) == {"k": 1}
    assert len(seen) == 2


async def test_connection_errors_are_retried_when_idempotent(
    make_client: Callable[..., Any],
) -> None:
    handler, seen = scripted(httpx.ConnectError("refused"), ok())
    client = make_client(handler, retry=RetryOptions(max_retries=1))
    assert await hash_abc(client) == {"digest": "00"}
    assert len(seen) == 2


async def test_connection_errors_are_not_retried_when_stateful(
    make_client: Callable[..., Any],
) -> None:
    handler, seen = scripted(httpx.ConnectError("refused"))
    client = make_client(handler, retry=RetryOptions(max_retries=3))
    with pytest.raises(TransportError) as caught:
        await call(client.ml_kem_generate_key_pair())
    assert not caught.value.timed_out
    assert isinstance(caught.value.__cause__, httpx.ConnectError)
    assert len(seen) == 1


async def test_timeouts_are_reported(make_client: Callable[..., Any]) -> None:
    handler, _ = scripted(httpx.ReadTimeout("slow"))
    with pytest.raises(TransportError) as caught:
        await hash_abc(make_client(handler))
    assert caught.value.timed_out


async def test_deadline_stops_retries(
    make_client: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    handler, seen = scripted(httpx.Response(503, headers={"retry-after": "2"}), ok())
    client = make_client(handler, deadline=1.0, retry=RetryOptions(max_retries=3))
    with pytest.raises(ApiError):
        await hash_abc(client)
    assert len(seen) == 1


async def test_deadline_already_passed(
    make_client: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = iter([100.0, 200.0])

    class FakeTime:
        monotonic = staticmethod(lambda: next(clock))

    monkeypatch.setattr(_core, "time", FakeTime)
    handler, seen = scripted(ok())
    with pytest.raises(TransportError) as caught:
        await hash_abc(make_client(handler, deadline=5.0))
    assert caught.value.timed_out
    assert seen == []


async def test_redirects_are_refused(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(307, headers={"location": "http://evil.test/"}))
    with pytest.raises(TransportError, match="redirect"):
        await hash_abc(make_client(handler))
    assert len(seen) == 1


async def test_malformed_success_body(make_client: Callable[..., Any]) -> None:
    handler, _ = scripted(httpx.Response(200, text="not json"))
    with pytest.raises(TransportError, match="not valid JSON"):
        await hash_abc(make_client(handler))


async def test_success_without_data(make_client: Callable[..., Any]) -> None:
    handler, _ = scripted(httpx.Response(200, json={"digest": "00"}))
    with pytest.raises(TransportError, match="no data member"):
        await hash_abc(make_client(handler))


async def test_bearer_token_and_traceparent(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(ok(), ok())
    client = make_client(handler, api_key=None, token="synthetic.jwt", traceparent=True)
    await hash_abc(client)
    await hash_abc(client)
    first, second = (request.headers for request in seen)
    assert first["authorization"] == "Bearer synthetic.jwt"
    assert "x-api-key" not in first
    pattern = r"00-[0-9a-f]{32}-[0-9a-f]{16}-01"
    assert re.fullmatch(pattern, first["traceparent"])
    assert first["traceparent"] != second["traceparent"]


async def test_static_traceparent(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(ok())
    value = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    await hash_abc(make_client(handler, traceparent=value))
    assert seen[0].headers["traceparent"] == value


async def test_raw_request_returns_any_status(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(
        httpx.Response(404, json=PROBLEM, headers={"content-type": "application/problem+json"}),
        httpx.Response(415, text="unsupported"),
    )
    client = make_client(handler)
    response = await call(client.request("get", "/v2/no-such-route", auth=False))
    assert response.status == 404
    assert response.media_type == "application/problem+json"
    assert response.json() == PROBLEM
    assert "x-api-key" not in seen[0].headers
    response = await call(
        client.request(
            "POST", "/v2/hash", content=b"<a/>", headers={"content-type": "application/xml"}
        )
    )
    assert response.status == 415
    assert seen[1].content == b"<a/>"
    assert seen[1].headers["content-type"] == "application/xml"
    assert seen[1].headers["x-api-key"]


async def test_raw_request_with_json_body(make_client: Callable[..., Any]) -> None:
    handler, seen = scripted(httpx.Response(200, json={"data": 1}))
    response = await call(make_client(handler).request("POST", "/v2/hash", body={"a": 1}))
    assert response.json() == {"data": 1}
    assert seen[0].content == b'{"a":1}'
    assert seen[0].headers["content-type"] == "application/json"


async def test_base_url_path_prefix(make_client: Callable[..., Any], kind: str) -> None:
    handler, seen = scripted(ok())
    from crypto_service import AsyncClient, Client

    transport = httpx.MockTransport(handler)
    if kind == "async":
        async with AsyncClient(BASE_URL + "/prefix/", transport=transport) as client:
            await hash_abc(client)
    else:
        with Client(BASE_URL + "/prefix/", transport=transport) as sync_client:
            await hash_abc(sync_client)
    assert seen[0].url.path == "/prefix/v2/hash"


async def test_repr_redacts_credentials(make_client: Callable[..., Any]) -> None:
    client = make_client(scripted()[0], token="synthetic.jwt")
    text = repr(client)
    assert "synthetic" not in text
    assert "'***'" in text
    assert BASE_URL in text


async def test_context_manager_closes_the_pool(kind: str) -> None:
    from crypto_service import AsyncClient, Client

    handler, _ = scripted()
    transport = httpx.MockTransport(handler)
    if kind == "async":
        async with AsyncClient(BASE_URL, transport=transport) as client:
            assert client._http.is_closed is False
        assert client._http.is_closed
    else:
        with Client(BASE_URL, transport=transport) as sync_client:
            assert sync_client._http.is_closed is False
        assert sync_client._http.is_closed
