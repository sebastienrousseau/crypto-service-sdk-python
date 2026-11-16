# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The SDK's exceptions and the RFC 9457 problem they carry.

Every exception derives from :class:`CryptoServiceError`. A response
with an error status raises :class:`ApiError`, whose
:attr:`ApiError.problem` is the server's problem document; a request
that got no usable response raises :class:`TransportError`.

Messages and ``repr`` hold the status, the problem type and its title,
never the request, the response body, the ``detail`` text or any
credential, so an exception can be logged without leaking data.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One member of a ``validation-failed`` problem's ``errors`` array."""

    field: str
    """The request member, as a JSON pointer or a body member name."""
    message: str = dataclasses.field(repr=False)
    """What is wrong with it."""


@dataclass(frozen=True, slots=True)
class Problem:
    """An RFC 9457 problem details document.

    A response whose body is not a problem (an HTML page from a proxy,
    an empty body) becomes an ``about:blank`` problem for its status, so
    every :class:`ApiError` has one.
    """

    type: str
    """``urn:crypto-service:problem:<slug>``, or ``about:blank``."""
    title: str
    """Short summary of the problem type."""
    status: int
    """HTTP status code."""
    detail: str = dataclasses.field(repr=False)
    """Explanation of this occurrence, meant for the caller."""
    instance: str | None = dataclasses.field(default=None, repr=False)
    """Request path of this occurrence."""
    code: str | None = None
    """Error code from crypto-lib, the key store or a KMS provider."""
    errors: tuple[ValidationIssue, ...] = dataclasses.field(default=(), repr=False)
    """Each request member that failed validation."""
    raw: Mapping[str, Any] = dataclasses.field(default_factory=dict, repr=False, compare=False)
    """The whole problem document as received, extension members included."""


class CryptoServiceError(Exception):
    """Base class of every exception the SDK raises."""


class ApiError(CryptoServiceError):
    """The server answered with an error status (4xx, 5xx).

    :attr:`problem` holds the RFC 9457 problem document.
    """

    problem: Problem

    def __init__(self, problem: Problem) -> None:
        super().__init__(f"HTTP {problem.status}: {problem.title} ({problem.type})")
        self.problem = problem

    @property
    def status(self) -> int:
        """HTTP status code of the response."""
        return self.problem.status

    @property
    def code(self) -> str | None:
        """The problem's ``code`` extension member, when it has one."""
        return self.problem.code


class TransportError(CryptoServiceError):
    """No usable response: the connection failed, the request timed out,
    the overall deadline passed, the server redirected, or a success
    response could not be decoded.

    The underlying exception, when there is one, is ``__cause__``.
    """

    timed_out: bool

    def __init__(self, message: str, *, timed_out: bool = False) -> None:
        super().__init__(message)
        self.timed_out = timed_out
