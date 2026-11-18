# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Hashing, MACs, key derivation and password hashing."""

from __future__ import annotations

from typing import cast

from .._core import compact
from ..encoding import Hex, to_hex
from ..types import (
    AlgorithmValidResult,
    Argon2Params,
    HashAlgorithm,
    HashResult,
    HmacAlgorithm,
    KdfAlgorithm,
    KdfParams,
    KdfResult,
    MacResult,
    PasswordHashResult,
    ValidResult,
)
from ._base import AsyncBase


class AsyncDigestOps(AsyncBase):
    """Routes that hash, authenticate or derive."""

    async def hash(self, *, algorithm: HashAlgorithm, data: str) -> HashResult:
        """``POST /v2/hash``: the hex digest of the UTF-8 text ``data``."""
        body = {"algorithm": algorithm, "data": data}
        return cast(HashResult, await self._call("POST", "/v2/hash", body, expect=HashResult))

    async def mac(self, *, algorithm: HmacAlgorithm, key: Hex, data: str) -> MacResult:
        """``POST /v2/hmac``: the hex HMAC of ``data`` under ``key``."""
        body = {"algorithm": algorithm, "key": to_hex(key), "data": data}
        return cast(MacResult, await self._call("POST", "/v2/hmac", body, expect=MacResult))

    async def mac_verify(
        self, *, algorithm: HmacAlgorithm, key: Hex, data: str, mac: Hex
    ) -> AlgorithmValidResult:
        """``POST /v2/hmac/verify``: whether ``mac`` is the HMAC of ``data``."""
        body = {"algorithm": algorithm, "key": to_hex(key), "data": data, "mac": to_hex(mac)}
        return cast(
            AlgorithmValidResult,
            await self._call("POST", "/v2/hmac/verify", body, expect=AlgorithmValidResult),
        )

    async def kdf(
        self,
        *,
        algorithm: KdfAlgorithm,
        password: str,
        salt: Hex | None = None,
        key_length: int | None = None,
        params: KdfParams | None = None,
    ) -> KdfResult:
        """``POST /v2/kdf``: derive a key (the server enforces OWASP floors)."""
        body = compact(
            {
                "algorithm": algorithm,
                "password": password,
                "salt": None if salt is None else to_hex(salt),
                "keyLength": key_length,
                "params": params,
            }
        )
        return cast(KdfResult, await self._call("POST", "/v2/kdf", body, expect=KdfResult))

    async def password_hash(
        self,
        *,
        password: str,
        time_cost: int | None = None,
        memory_cost: int | None = None,
        parallelism: int | None = None,
    ) -> PasswordHashResult:
        """``POST /v2/password/hash``: Argon2id (at least 2 passes, 19456 KiB)."""
        body = compact(
            {
                "password": password,
                "timeCost": time_cost,
                "memoryCost": memory_cost,
                "parallelism": parallelism,
            }
        )
        return cast(
            PasswordHashResult,
            await self._call("POST", "/v2/password/hash", body, expect=PasswordHashResult),
        )

    async def password_verify(
        self, *, password: str, hash: Hex, salt: Hex, params: Argon2Params
    ) -> ValidResult:
        """``POST /v2/password/verify``: check a password against an Argon2id hash."""
        body = {"password": password, "hash": to_hex(hash), "salt": to_hex(salt), "params": params}
        return cast(
            ValidResult, await self._call("POST", "/v2/password/verify", body, expect=ValidResult)
        )
