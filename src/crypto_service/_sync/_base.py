# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
# Generated from src/crypto_service/_async/_base.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Connection pool, retries and deadlines of the blocking client."""

from __future__ import annotations

import time
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from .. import _core
from .._core import RetryOptions
from .._response import Response
from ..errors import TransportError

_sleep = time.sleep
_attempt_scope = _core.blocking_scope


class Base:
    """Sends requests for the operation mixins; see :class:`Client`."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        token: str | None = None,
        timeout: float | None = _core.DEFAULT_TIMEOUT,
        deadline: float | None = None,
        retry: RetryOptions | None = None,
        traceparent: str | bool | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._config = _core.Config.create(
            base_url,
            api_key=api_key,
            token=token,
            timeout=timeout,
            deadline=deadline,
            retry=retry,
            traceparent=traceparent,
        )
        # One pool per client: keep-alive, HTTP/2 over TLS when the server
        # offers it, never a redirect, TLS verification left on.
        self._http = httpx.Client(
            base_url=self._config.base_url,
            http2=True,
            follow_redirects=False,
            transport=transport,
        )

    def __repr__(self) -> str:
        return self._config.describe(type(self).__name__)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the connection pool. The client cannot be used afterwards."""
        self._http.close()

    def _attempt(
        self,
        method: str,
        path: str,
        content: bytes | None,
        headers: dict[str, str],
        deadline: _core.Deadline,
    ) -> httpx.Response:
        budget = deadline.budget(self._config.timeout)
        try:
            with _attempt_scope(budget):
                return self._http.request(
                    method, path, content=content, headers=headers, timeout=budget
                )
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise TransportError("The request timed out", timed_out=True) from exc
        except httpx.HTTPError as exc:
            raise TransportError("No response: the connection failed") from exc

    def _send(
        self,
        method: str,
        path: str,
        content: bytes | None,
        headers: dict[str, str],
    ) -> httpx.Response:
        retry = self._config.retry
        idempotent = _core.is_idempotent(method, path)
        deadline = _core.Deadline(self._config.deadline)
        attempt = 0
        while True:
            attempt += 1
            try:
                response = self._attempt(method, path, content, headers, deadline)
            except TransportError:
                delay = _core.delay_after_error(attempt, retry, idempotent)
                if delay is None or not deadline.allows(delay):
                    raise
            else:
                retry_after = response.headers.get("retry-after")
                delay = _core.delay_after_status(
                    response.status_code, retry_after, attempt, retry, idempotent
                )
                if delay is None or not deadline.allows(delay):
                    return response
            _sleep(delay)

    def _call(
        self,
        method: str,
        path: str,
        body: Mapping[str, Any] | None = None,
        *,
        expect: Any,
        wrapped: bool = True,
        auth: bool = True,
    ) -> Any:
        content = None if body is None else _core.encode_body(body)
        headers = self._config.headers(auth=auth, has_body=content is not None)
        response = self._send(method, path, content, headers)
        return _core.decode_response(
            response.status_code,
            response.reason_phrase,
            response.content,
            wrapped=wrapped,
            expected=expect,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Mapping[str, Any] | None = None,
        content: bytes | None = None,
        headers: Mapping[str, str] | None = None,
        auth: bool = True,
    ) -> Response:
        """Send any request and return the response, whatever its status.

        For routes without a typed method. ``body`` is sent as JSON;
        ``content`` is sent as it is, with the media type in ``headers``.
        Retries, timeouts and the deadline apply as for typed methods; a
        missing response still raises :class:`TransportError`. ``path``
        is relative to ``base_url``: one with a scheme or a host, a
        method that is not an HTTP token, or a header that is not
        visible ASCII raises ``ValueError`` before anything is sent.
        """
        _core.check_request_target(method, path)
        if body is not None:
            content = _core.encode_body(body)
        merged = self._config.headers(auth=auth, has_body=body is not None, extra=headers)
        response = self._send(method.upper(), path, content, merged)
        return Response(response.status_code, response.headers, response.content)
