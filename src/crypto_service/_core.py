# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Transport-agnostic request logic shared by the async and sync clients.

Nothing here performs I/O: it validates options, builds headers, encodes
request bodies, decodes responses and decides whether and when to retry.
The two clients differ only in how they wait and send, so every rule
lives once, here, and is tested once.
"""

from __future__ import annotations

import contextlib
import json
import math
import re
import secrets
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

from ._problem import parse_problem
from ._shape import check_shape
from ._version import USER_AGENT
from .errors import ApiError, TransportError

DEFAULT_TIMEOUT = 30.0
"""Seconds allowed for one attempt, unless the client says otherwise."""

#: Routes that create or delete server state. After a lost connection or
#: a 504 the server may already have done the work, so these are retried
#: only when it certainly did not (429, 503). Same table as the
#: TypeScript SDK's request.ts.
_STATEFUL_ROUTE = re.compile(r"/(keygen|keys/generate|keys/delete|kms/create-key|opaque/register/)")
_TRANSIENT = frozenset({429, 503, 504})
# Allowlists for what reaches a request line or a header (RFC 9110,
# RFC 7235, W3C Trace Context), ASCII only: anything else is refused
# before a request is built, and the message never repeats the value.
#: A field value: visible ASCII, inner spaces and tabs allowed.
_FIELD_VALUE = re.compile(r"[\x21-\x7e](?:[\x21-\x7e \t]*[\x21-\x7e])?")
#: The credentials of the Bearer scheme (token68).
_TOKEN68 = re.compile(r"[A-Za-z0-9._~+/-]+=*")
#: A method or a field name (an RFC 9110 token).
_TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")
#: A traceparent: version (not ff), non-zero trace and parent IDs, flags.
_TRACEPARENT = re.compile(
    r"(?!ff)[0-9a-f]{2}-(?!0{32})[0-9a-f]{32}-(?!0{16})[0-9a-f]{16}-[0-9a-f]{2}"
)
#: A request target: visible ASCII, no spaces or control characters.
_TARGET = re.compile(r"[\x21-\x7e]+")
_REDACTED = "'***'"
_JITTER = secrets.SystemRandom().random


@dataclass(frozen=True, slots=True)
class RetryOptions:
    """When and how long to wait before repeating a failed request.

    Retries are off by default (``max_retries=0``). A retried request
    waits a random time in ``[0, min(initial_delay * 2**(n-1), max_delay)]``
    (exponential backoff with full jitter), or what the server's
    ``Retry-After`` asks for; a ``Retry-After`` longer than ``max_delay``
    ends the retries.
    """

    max_retries: int = 0
    """Retries after the first attempt."""
    initial_delay: float = 0.2
    """Seconds: the backoff cap before the first retry."""
    max_delay: float = 2.0
    """Seconds: the longest wait, computed or asked for."""

    def __post_init__(self) -> None:
        if self.max_retries < 0 or self.initial_delay < 0 or self.max_delay < 0:
            raise ValueError("retry options must not be negative")


def _check(name: str, value: str | None, pattern: re.Pattern[str], rule: str) -> None:
    if value is not None and pattern.fullmatch(value) is None:
        raise ValueError(f"{name} must be {rule}")


def check_request_target(method: str, path: str) -> None:
    """Refuse a raw request whose method or path is not a plain origin-relative target.

    A path with a scheme or a host (``https://other.test/``,
    ``//other.test/``) would send the credentials to another origin.
    """
    _check("method", method, _TOKEN, "an HTTP token such as GET or POST")
    parts = urlsplit(path) if _TARGET.fullmatch(path) else None
    if parts is None or parts.scheme or parts.netloc:
        raise ValueError("path must be a path on base_url, without a scheme, host or spaces")


def _check_extra_headers(extra: Mapping[str, str]) -> None:
    for name, value in extra.items():
        _check("a header name", name, _TOKEN, "an HTTP token")
        _check("a header value", value, _FIELD_VALUE, "visible ASCII")


def _check_base_url(base_url: str) -> str:
    parts = urlsplit(base_url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("base_url must be an http:// or https:// URL with a host")
    if parts.username is not None or parts.password is not None:
        raise ValueError("base_url must not carry credentials; use api_key or token")
    if parts.query or parts.fragment:
        raise ValueError("base_url must not have a query or a fragment")
    return base_url.rstrip("/")


@dataclass(frozen=True, slots=True)
class Config:
    """A client's validated, immutable configuration."""

    base_url: str
    api_key: str | None = field(default=None, repr=False)
    token: str | None = field(default=None, repr=False)
    timeout: float | None = DEFAULT_TIMEOUT
    deadline: float | None = None
    retry: RetryOptions = RetryOptions()
    traceparent: str | bool | None = None

    @classmethod
    def create(
        cls,
        base_url: str,
        *,
        api_key: str | None,
        token: str | None,
        timeout: float | None,
        deadline: float | None,
        retry: RetryOptions | None,
        traceparent: str | bool | None,
    ) -> Config:
        """Validate the options and build the configuration."""
        _check("api_key", api_key, _FIELD_VALUE, "visible ASCII (inner spaces allowed)")
        _check("token", token, _TOKEN68, "a token68 string, such as a JWT")
        if isinstance(traceparent, str):
            _check("traceparent", traceparent, _TRACEPARENT, "a W3C traceparent")
        if (timeout is not None and timeout <= 0) or (deadline is not None and deadline <= 0):
            raise ValueError("timeout and deadline must be positive seconds, or None")
        return cls(
            base_url=_check_base_url(base_url),
            api_key=api_key,
            token=token,
            timeout=timeout,
            deadline=deadline,
            retry=retry or RetryOptions(),
            traceparent=traceparent,
        )

    def describe(self, cls_name: str) -> str:
        """A ``repr`` for the client: credentials show as ``'***'``."""
        api_key = _REDACTED if self.api_key else "None"
        token = _REDACTED if self.token else "None"
        return f"{cls_name}(base_url={self.base_url!r}, api_key={api_key}, token={token})"

    def headers(
        self, *, auth: bool, has_body: bool, extra: Mapping[str, str] | None = None
    ) -> dict[str, str]:
        """The headers of one request: identity, credentials, trace context."""
        headers = {"accept": "application/json", "user-agent": USER_AGENT}
        if has_body:
            headers["content-type"] = "application/json"
        if auth and self.api_key:
            headers["x-api-key"] = self.api_key
        if auth and self.token:
            headers["authorization"] = f"Bearer {self.token}"
        if self.traceparent is True:
            headers["traceparent"] = generate_traceparent()
        elif isinstance(self.traceparent, str):
            headers["traceparent"] = self.traceparent
        if extra:
            _check_extra_headers(extra)
            headers.update(extra)
        return headers


def generate_traceparent() -> str:
    """A fresh W3C Trace Context ``traceparent``, version 00, sampled."""
    trace_id = bytearray(secrets.token_bytes(16))
    parent_id = bytearray(secrets.token_bytes(8))
    # All-zero IDs are invalid: force a non-zero first byte.
    trace_id[0] = trace_id[0] % 255 + 1
    parent_id[0] = parent_id[0] % 255 + 1
    return f"00-{trace_id.hex()}-{parent_id.hex()}-01"


def is_idempotent(method: str, path: str) -> bool:
    """Whether repeating ``method path`` cannot create or delete anything twice."""
    return method == "GET" or _STATEFUL_ROUTE.search(path) is None


def retry_after_seconds(header: str | None, now: float) -> float | None:
    """Seconds a ``Retry-After`` value asks for (delta-seconds or HTTP-date)."""
    if header is None or not header.strip():
        return None
    try:
        seconds = float(header)
    except ValueError:
        return _http_date_delay(header, now)
    return seconds if math.isfinite(seconds) and seconds >= 0 else None


def _http_date_delay(header: str, now: float) -> float | None:
    try:
        when = parsedate_to_datetime(header)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, when.timestamp() - now)


def backoff_delay(
    attempt: int,
    retry: RetryOptions,
    retry_after: str | None = None,
    *,
    rand: Callable[[], float] = _JITTER,
) -> float | None:
    """Seconds to wait after attempt ``attempt`` (from 1), or None to stop.

    The server's ``Retry-After`` wins when present; one longer than
    ``max_delay`` means do not retry.
    """
    asked = retry_after_seconds(retry_after, time.time())
    if asked is not None:
        return asked if asked <= retry.max_delay else None
    cap = min(retry.initial_delay * 2.0 ** min(attempt - 1, 62), retry.max_delay)
    return rand() * cap


def delay_after_error(attempt: int, retry: RetryOptions, idempotent: bool) -> float | None:
    """Wait before retrying a request that got no response, or None."""
    if not idempotent or attempt > retry.max_retries:
        return None
    return backoff_delay(attempt, retry)


def delay_after_status(
    status: int, retry_after: str | None, attempt: int, retry: RetryOptions, idempotent: bool
) -> float | None:
    """Wait before retrying a request answered with ``status``, or None.

    429, 503 and 504 are transient. A 504 may have been processed
    upstream, so a stateful request is not repeated after one.
    """
    if attempt > retry.max_retries or status not in _TRANSIENT:
        return None
    if status == 504 and not idempotent:
        return None
    return backoff_delay(attempt, retry, retry_after)


class Deadline:
    """The overall time limit of one call, retries and waits included."""

    __slots__ = ("_end",)

    def __init__(self, seconds: float | None) -> None:
        self._end = None if seconds is None else time.monotonic() + seconds

    def budget(self, timeout: float | None) -> float | None:
        """Seconds the next attempt may take; raises once the deadline passed."""
        if self._end is None:
            return timeout
        remaining = self._end - time.monotonic()
        if remaining <= 0:
            raise TransportError("The call's deadline passed", timed_out=True)
        return remaining if timeout is None else min(timeout, remaining)

    def allows(self, delay: float) -> bool:
        """Whether waiting ``delay`` seconds still leaves time to try again."""
        return self._end is None or time.monotonic() + delay < self._end


def blocking_scope(_seconds: float | None) -> contextlib.nullcontext[None]:
    """The blocking client's per-attempt scope: httpx's own timeouts apply."""
    return contextlib.nullcontext()


def encode_body(body: Mapping[str, Any]) -> bytes:
    """A request body as compact UTF-8 JSON."""
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def decode_success(content: bytes, *, wrapped: bool, expected: Any = Any) -> Any:
    """The value of a 2xx JSON body: its ``data`` member when ``wrapped``.

    The value is checked against ``expected``, a :mod:`crypto_service.types`
    type (``Any`` checks nothing), before it is returned.
    """
    try:
        value = json.loads(content)
    except (ValueError, RecursionError) as exc:
        raise TransportError("The server's response is not valid JSON") from exc
    if not wrapped:
        return check_shape(value, expected, "body")
    if not isinstance(value, dict) or "data" not in value:
        raise TransportError("The server's response has no data member")
    return check_shape(value["data"], expected)


def decode_response(
    status: int, reason: str, content: bytes, *, wrapped: bool, expected: Any = Any
) -> Any:
    """Decode a final response, or raise the error it stands for."""
    if 300 <= status < 400:
        raise TransportError("The server answered with a redirect, which the client refuses")
    if status >= 400:
        raise ApiError(parse_problem(status, reason, content))
    return decode_success(content, wrapped=wrapped, expected=expected)


def compact(members: Mapping[str, Any]) -> dict[str, Any]:
    """A request body without the optional members left as None."""
    return {name: value for name, value in members.items() if value is not None}
