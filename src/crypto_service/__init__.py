# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Typed Python client for the Crypto Service REST API (crypto-server v2).

The SDK is a thin client: every operation is an HTTP call to a
crypto-server, and no cryptography runs in this package.
:class:`AsyncClient` is the primary API; :class:`Client` is its blocking
twin, generated from the same source.
"""

from ._async._client import AsyncClient
from ._core import RetryOptions
from ._response import Response
from ._sync._client import Client
from ._version import USER_AGENT, __version__
from .errors import ApiError, CryptoServiceError, Problem, TransportError, ValidationIssue

__all__ = [
    "USER_AGENT",
    "ApiError",
    "AsyncClient",
    "Client",
    "CryptoServiceError",
    "Problem",
    "Response",
    "RetryOptions",
    "TransportError",
    "ValidationIssue",
    "__version__",
]
