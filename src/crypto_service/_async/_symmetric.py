# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Symmetric encryption: AEAD, secretbox, password envelopes and AES key wrap."""

from __future__ import annotations

from typing import cast

from .._core import compact
from ..encoding import Base64, Hex, to_base64, to_hex
from ..types import (
    AeadResult,
    KeyWrapAlgorithm,
    KeyWrapResult,
    PasswordEncryptResult,
    PlaintextResult,
    SealedResult,
)
from ._base import AsyncBase


class AsyncSymmetricOps(AsyncBase):
    """Routes keyed by a caller-held symmetric key or a password."""

    async def encrypt(self, *, key: Hex, plaintext: str) -> AeadResult:
        """``POST /v2/encrypt``: XChaCha20-Poly1305 under a 256-bit key.

        ``key`` is 32 bytes (or 64 hex characters); ``ciphertext`` comes
        back as base64.
        """
        body = {"key": to_hex(key), "plaintext": plaintext}
        return cast(AeadResult, await self._call("POST", "/v2/encrypt", body, expect=AeadResult))

    async def decrypt(self, *, key: Hex, ciphertext: Base64) -> PlaintextResult:
        """``POST /v2/decrypt``: the UTF-8 plaintext of an ``encrypt`` ciphertext."""
        body = {"key": to_hex(key), "ciphertext": to_base64(ciphertext)}
        return cast(
            PlaintextResult, await self._call("POST", "/v2/decrypt", body, expect=PlaintextResult)
        )

    async def secretbox_seal(
        self, *, key: Hex, plaintext: str, aad: str | None = None
    ) -> SealedResult:
        """``POST /v2/secretbox/seal``: authenticated encryption with optional AAD."""
        body = compact({"key": to_hex(key), "plaintext": plaintext, "aad": aad})
        return cast(
            SealedResult, await self._call("POST", "/v2/secretbox/seal", body, expect=SealedResult)
        )

    async def secretbox_open(self, *, key: Hex, ciphertext: Base64, aad: str | None = None) -> str:
        """``POST /v2/secretbox/open``: the UTF-8 plaintext (``data`` is a bare string)."""
        body = compact({"key": to_hex(key), "ciphertext": to_base64(ciphertext), "aad": aad})
        return cast(str, await self._call("POST", "/v2/secretbox/open", body, expect=str))

    async def password_encrypt(self, *, password: str, plaintext: str) -> PasswordEncryptResult:
        """``POST /v2/password/encrypt``: Argon2id + XChaCha20-Poly1305 envelope."""
        body = {"password": password, "plaintext": plaintext}
        return cast(
            PasswordEncryptResult,
            await self._call("POST", "/v2/password/encrypt", body, expect=PasswordEncryptResult),
        )

    async def password_decrypt(self, *, password: str, ciphertext: Base64) -> str:
        """``POST /v2/password/decrypt``: the plaintext of a ``password_encrypt`` envelope."""
        body = {"password": password, "ciphertext": to_base64(ciphertext)}
        return cast(str, await self._call("POST", "/v2/password/decrypt", body, expect=str))

    async def key_wrap(
        self, *, kek: Hex, key_to_wrap: Hex, algorithm: KeyWrapAlgorithm | None = None
    ) -> KeyWrapResult:
        """``POST /v2/keys/wrap``: AES-KW (RFC 3394) or AES-KWP (RFC 5649)."""
        body = compact(
            {"kek": to_hex(kek), "keyToWrap": to_hex(key_to_wrap), "algorithm": algorithm}
        )
        return cast(
            KeyWrapResult, await self._call("POST", "/v2/keys/wrap", body, expect=KeyWrapResult)
        )

    async def key_unwrap(
        self, *, kek: Hex, wrapped_key: Base64, algorithm: KeyWrapAlgorithm | None = None
    ) -> str:
        """``POST /v2/keys/unwrap``: the unwrapped key as hex (``data`` is a bare string)."""
        body = compact(
            {"kek": to_hex(kek), "wrappedKey": to_base64(wrapped_key), "algorithm": algorithm}
        )
        return cast(str, await self._call("POST", "/v2/keys/unwrap", body, expect=str))
