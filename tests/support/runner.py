# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Run the conformance kit against a live crypto-server through the SDK.

Each vector goes through the typed :class:`~crypto_service.AsyncClient`
method for its route when one exists and its body binds to that
method's keyword arguments (members renamed from camelCase); otherwise,
for v1, ``/metrics``, unknown routes and deliberately malformed
requests, through :meth:`~crypto_service.AsyncClient.request`. A
recording transport keeps the status, media type and headers of each
response; the body compared with the template is what the SDK returned
(wrapped back in ``data``) or the problem an :class:`ApiError` carries.

Each file runs as its own principal, ``conformance-<group>``, with an
HS256 token minted from the server's ``JWT_SECRET`` (kit README).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from crypto_service import ApiError, AsyncClient

from ..operations import OPS
from .kit import mismatches, pointer, substitute

#: (HTTP method, path) to the typed method that sends it.
ROUTES: dict[tuple[str, str], tuple[str, bool]] = {
    (op.method, op.path): (op.name, op.wrapped) for op in OPS
}
_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(frozen=True)
class LiveServer:
    """Where the kit runs and how to authenticate."""

    url: str
    api_key: str
    jwt_secret: str
    issuer: str | None = None
    audience: str | None = None


@dataclass
class Outcome:
    status: int
    media_type: str
    headers: httpx.Headers
    body: Any
    via: str


@dataclass
class FileResult:
    name: str
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


class Recorder(httpx.AsyncBaseTransport):
    """An HTTP transport that remembers the last response's head."""

    def __init__(self) -> None:
        self._inner = httpx.AsyncHTTPTransport(http2=True)
        self.last: httpx.Response | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.last = await self._inner.handle_async_request(request)
        return self.last

    async def aclose(self) -> None:
        await self._inner.aclose()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def mint(server: LiveServer, sub: str, scopes: list[str]) -> str:
    """An HS256 JWT for ``sub`` with exactly ``scopes`` (test credential)."""
    now = int(time.time())
    claims: dict[str, Any] = {"sub": sub, "scopes": scopes, "iat": now, "exp": now + 300}
    if server.issuer:
        claims["iss"] = server.issuer
    if server.audience:
        claims["aud"] = server.audience
    head = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    signing_input = f"{head}.{_b64url(json.dumps(claims).encode())}"
    mac = hmac.new(server.jwt_secret.encode(), signing_input.encode(), hashlib.sha256)
    return f"{signing_input}.{_b64url(mac.digest())}"


class Clients:
    """One SDK client per credential a file uses."""

    def __init__(self, server: LiveServer, group: str) -> None:
        self._server = server
        self._sub = f"conformance-{group}"
        self._made: dict[str, tuple[AsyncClient, Recorder]] = {}

    def get(self, auth: Any) -> tuple[AsyncClient, Recorder]:
        key = json.dumps(auth, sort_keys=True)
        if key not in self._made:
            recorder = Recorder()
            token = None
            if auth != "none":
                scopes = ["crypto:admin"] if auth in (None, "admin") else auth["scopes"]
                token = mint(self._server, self._sub, scopes)
            client = AsyncClient(self._server.url, token=token, transport=recorder)
            self._made[key] = (client, recorder)
        return self._made[key]

    async def aclose(self) -> None:
        for client, _ in self._made.values():
            await client.aclose()


def _kwargs(body: Any) -> dict[str, Any] | None:
    if body is None:
        return {}
    if not isinstance(body, dict):
        return None
    return {_CAMEL.sub("_", key).lower(): value for key, value in body.items()}


def _typed_call(client: AsyncClient, request: dict[str, Any]) -> tuple[Any, bool] | None:
    """The coroutine of the typed method for this request, if it binds."""
    route = ROUTES.get((request["method"], request["path"]))
    kwargs = _kwargs(request.get("body"))
    if route is None or kwargs is None or "rawBody" in request or "headers" in request:
        return None
    method = getattr(client, route[0])
    try:
        inspect.signature(method).bind(**kwargs)
    except TypeError:
        return None
    return method(**kwargs), route[1]


async def _send(client: AsyncClient, recorder: Recorder, request: dict[str, Any]) -> Outcome:
    typed = _typed_call(client, request)
    if typed is None:
        content = request.get("rawBody", "").encode() if "rawBody" in request else None
        response = await client.request(
            request["method"],
            request["path"],
            body=request.get("body"),
            content=content,
            headers=request.get("headers"),
        )
        body = (
            response.json() if response.media_type.endswith("json") else response.content.decode()
        )
        return Outcome(
            response.status, response.media_type, httpx.Headers(response.headers), body, "raw"
        )
    coroutine, wrapped = typed
    try:
        value = await coroutine
    except ApiError as error:
        body = dict(error.problem.raw)
    else:
        body = {"data": value} if wrapped else value
    assert recorder.last is not None
    head = recorder.last
    media_type = head.headers.get("content-type", "").split(";")[0].strip()
    return Outcome(head.status_code, media_type, head.headers, body, "typed")


def _check(vector: dict[str, Any], outcome: Outcome, captured: dict[str, str]) -> list[str]:
    expect = substitute(vector["expect"], captured)
    problems = []
    if outcome.status != expect["status"]:
        problems.append(f"status {outcome.status} != {expect['status']}")
    if outcome.media_type != expect["mediaType"]:
        problems.append(f"media type {outcome.media_type} != {expect['mediaType']}")
    for name, value in expect.get("headers", {}).items():
        if outcome.headers.get(name) != value:
            problems.append(f"header {name}: {outcome.headers.get(name)!r} != {value!r}")
    template = expect["body"] if "body" in expect else expect.get("text")
    if template is not None:
        problems += mismatches(template, outcome.body)
    return problems


async def run_file(server: LiveServer, name: str, document: dict[str, Any]) -> FileResult:
    """Run one vector file in order; captures carry over within it."""
    result = FileResult(name)
    captured: dict[str, str] = {}
    clients = Clients(server, document["group"])
    try:
        for vector in document["vectors"]:
            request = substitute(vector["request"], captured)
            client, recorder = clients.get(vector.get("auth"))
            outcome = await _send(client, recorder, request)
            problems = _check(vector, outcome, captured)
            label = f"{vector['id']} ({outcome.via})"
            if problems:
                result.failed.append(f"{label}: " + "; ".join(problems))
                continue
            result.passed.append(label)
            for capture, at in vector.get("capture", {}).items():
                captured[capture] = str(pointer(outcome.body, at))
    finally:
        await clients.aclose()
    return result
