# SPDX-License-Identifier: Apache-2.0 OR MIT
# Generated from src/crypto_service/_async/_client.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""The blocking client."""

from __future__ import annotations

from ._digest import DigestOps
from ._keys import KeyOps
from ._kms import KmsOps
from ._meta import MetaOps
from ._opaque import OpaqueOps
from ._pq import PqOps
from ._sealed import SealedOps
from ._symmetric import SymmetricOps


class Client(
    MetaOps,
    DigestOps,
    SymmetricOps,
    KeyOps,
    PqOps,
    SealedOps,
    KmsOps,
    OpaqueOps,
):
    """Blocking client for the crypto-server v2 API.

    One instance holds one connection pool (keep-alive, HTTP/2 over TLS
    when offered). Share it between threads in one process and close it
    with ``with`` or :meth:`close`.

    Args:
        base_url: Server root, ``http://`` or ``https://``.
        api_key: Sent as ``x-api-key``.
        token: A JWT, sent as ``Authorization: Bearer``.
        timeout: Seconds per attempt (default 30); None for none.
        deadline: Seconds for the whole call, retries and waits included.
        retry: :class:`RetryOptions`; retries are off by default.
        traceparent: A W3C ``traceparent`` to send, or True for a new
            one per call.
        transport: An ``httpx.BaseTransport``, for tests.

    Example:
        >>> with Client("http://127.0.0.1:3000", api_key=key) as client:
        ...     result = client.hash(algorithm="sha256", data="abc")
    """
