# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Server-held keys and Ed25519 signatures, singly and in batches."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from .._core import compact
from ..encoding import Hex, to_hex
from ..types import (
    AlgorithmValidResult,
    DeletedKey,
    ExportedKey,
    GeneratedKey,
    KeyAlgorithm,
    KeyMetadata,
    SignatureResult,
    StreamSignItem,
    StreamSignResult,
    StreamVerifyItem,
    StreamVerifyResult,
)
from ._base import AsyncBase


class AsyncKeyOps(AsyncBase):
    """Key lifecycle and classical signatures.

    Private keys stay on the server: generation returns a ``keyId`` and
    the public key, and signing takes the ``keyId``.
    """

    async def generate_key_pair(
        self, *, algorithm: KeyAlgorithm | None = None, metadata: KeyMetadata | None = None
    ) -> GeneratedKey:
        """``POST /v2/keys/generate``: a server-held key pair (Ed25519 by default).

        Stateful: retried only after 429 or 503, never after a lost
        connection or a 504.
        """
        body = compact({"algorithm": algorithm, "metadata": metadata})
        return cast(
            GeneratedKey, await self._call("POST", "/v2/keys/generate", body, expect=GeneratedKey)
        )

    async def export_key(self, *, key_id: str) -> ExportedKey:
        """``POST /v2/keys/export``: the key, private parts included.

        Needs the ``crypto:keys:export`` scope, which ``crypto:admin``
        does not imply.
        """
        return cast(
            ExportedKey,
            await self._call("POST", "/v2/keys/export", {"keyId": key_id}, expect=ExportedKey),
        )

    async def keys_delete(self, *, key_id: str) -> DeletedKey:
        """``POST /v2/keys/delete``: remove a server-held key (stateful)."""
        return cast(
            DeletedKey,
            await self._call("POST", "/v2/keys/delete", {"keyId": key_id}, expect=DeletedKey),
        )

    async def sign(self, *, key_id: str, message: str) -> SignatureResult:
        """``POST /v2/sign``: an Ed25519 signature of the UTF-8 ``message``."""
        body = {"keyId": key_id, "message": message}
        return cast(
            SignatureResult, await self._call("POST", "/v2/sign", body, expect=SignatureResult)
        )

    async def verify(
        self, *, public_key: Hex, message: str, signature: Hex
    ) -> AlgorithmValidResult:
        """``POST /v2/verify``: check an Ed25519 signature under a public key."""
        body = {"publicKey": to_hex(public_key), "message": message, "signature": to_hex(signature)}
        return cast(
            AlgorithmValidResult,
            await self._call("POST", "/v2/verify", body, expect=AlgorithmValidResult),
        )

    async def stream_sign(self, *, items: Sequence[StreamSignItem]) -> StreamSignResult:
        """``POST /v2/stream/sign``: sign many messages with server-held keys."""
        body = {"items": list(items)}
        return cast(
            StreamSignResult,
            await self._call("POST", "/v2/stream/sign", body, expect=StreamSignResult),
        )

    async def stream_verify(self, *, items: Sequence[StreamVerifyItem]) -> StreamVerifyResult:
        """``POST /v2/stream/verify``: check many Ed25519 signatures."""
        body = {"items": list(items)}
        return cast(
            StreamVerifyResult,
            await self._call("POST", "/v2/stream/verify", body, expect=StreamVerifyResult),
        )
