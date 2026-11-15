# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The asynchronous client."""

from __future__ import annotations

from ._digest import AsyncDigestOps
from ._keys import AsyncKeyOps
from ._kms import AsyncKmsOps
from ._meta import AsyncMetaOps
from ._opaque import AsyncOpaqueOps
from ._pq import AsyncPqOps
from ._sealed import AsyncSealedOps
from ._symmetric import AsyncSymmetricOps


class AsyncClient(
    AsyncMetaOps,
    AsyncDigestOps,
    AsyncSymmetricOps,
    AsyncKeyOps,
    AsyncPqOps,
    AsyncSealedOps,
    AsyncKmsOps,
    AsyncOpaqueOps,
):
    """Asynchronous client for the crypto-server v2 API.

    One instance holds one connection pool (keep-alive, HTTP/2 over TLS
    when offered). Share it between tasks on one event loop and close it
    with ``async with`` or :meth:`aclose`.

    Args:
        base_url: Server root, ``http://`` or ``https://``.
        api_key: Sent as ``x-api-key``.
        token: A JWT, sent as ``Authorization: Bearer``.
        timeout: Seconds per attempt (default 30); None for none.
        deadline: Seconds for the whole call, retries and waits included.
        retry: :class:`RetryOptions`; retries are off by default.
        traceparent: A W3C ``traceparent`` to send, or True for a new
            one per call.
        transport: An ``httpx.AsyncBaseTransport``, for tests.

    Example:
        >>> async with AsyncClient("http://127.0.0.1:3000", api_key=key) as client:
        ...     result = await client.hash(algorithm="sha256", data="abc")
    """
