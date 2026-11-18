# SPDX-License-Identifier: Apache-2.0 OR MIT
# Generated from src/crypto_service/_async/_kms.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Key management service routes (local provider by default)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from .._core import compact
from ..encoding import Hex, to_hex
from ..types import (
    KmsDataKey,
    KmsDecryptResult,
    KmsEncoding,
    KmsEncryptResult,
    KmsKey,
    KmsUnwrapResult,
    KmsUsage,
    KmsWrapResult,
)
from ._base import Base


class KmsOps(Base):
    """KMS keys live with the provider; ciphertexts and wrapped keys are
    opaque provider strings, passed back unchanged.
    """

    def kms_create_key(
        self,
        *,
        provider: str | None = None,
        algorithm: str | None = None,
        usage: KmsUsage | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> KmsKey:
        """``POST /v2/kms/create-key``: a managed key (stateful)."""
        body = compact(
            {"provider": provider, "algorithm": algorithm, "usage": usage, "metadata": metadata}
        )
        return cast(KmsKey, self._call("POST", "/v2/kms/create-key", body, expect=KmsKey))

    def kms_encrypt(
        self,
        *,
        key_id: str,
        plaintext: str | bytes,
        encoding: KmsEncoding | None = None,
        provider: str | None = None,
        context: Mapping[str, str] | None = None,
    ) -> KmsEncryptResult:
        """``POST /v2/kms/encrypt``.

        The server reads ``plaintext`` as UTF-8 unless ``encoding`` is
        ``"hex"``. ``bytes`` are sent as hex with ``encoding="hex"``; a
        ``str`` is sent with the ``encoding`` given (the server's default
        when None). The encoding is never guessed from the content.
        """
        if isinstance(plaintext, bytes):
            plaintext, encoding = plaintext.hex(), "hex"
        body = compact(
            {
                "keyId": key_id,
                "plaintext": plaintext,
                "encoding": encoding,
                "provider": provider,
                "context": context,
            }
        )
        return cast(
            KmsEncryptResult,
            self._call("POST", "/v2/kms/encrypt", body, expect=KmsEncryptResult),
        )

    def kms_decrypt(
        self,
        *,
        key_id: str,
        ciphertext: str,
        provider: str | None = None,
        context: Mapping[str, str] | None = None,
    ) -> KmsDecryptResult:
        """``POST /v2/kms/decrypt``: the plaintext as UTF-8 text and as hex."""
        body = compact(
            {"keyId": key_id, "ciphertext": ciphertext, "provider": provider, "context": context}
        )
        return cast(
            KmsDecryptResult,
            self._call("POST", "/v2/kms/decrypt", body, expect=KmsDecryptResult),
        )

    def kms_wrap(
        self,
        *,
        key_id: str,
        unwrapped_key: Hex,
        provider: str | None = None,
        context: Mapping[str, str] | None = None,
    ) -> KmsWrapResult:
        """``POST /v2/kms/wrap``: wrap key bytes under a managed key."""
        body = compact(
            {
                "keyId": key_id,
                "unwrappedKey": to_hex(unwrapped_key),
                "provider": provider,
                "context": context,
            }
        )
        return cast(KmsWrapResult, self._call("POST", "/v2/kms/wrap", body, expect=KmsWrapResult))

    def kms_unwrap(
        self,
        *,
        key_id: str,
        wrapped_key: str,
        provider: str | None = None,
        context: Mapping[str, str] | None = None,
    ) -> KmsUnwrapResult:
        """``POST /v2/kms/unwrap``: the key bytes as hex."""
        body = compact(
            {"keyId": key_id, "wrappedKey": wrapped_key, "provider": provider, "context": context}
        )
        return cast(
            KmsUnwrapResult,
            self._call("POST", "/v2/kms/unwrap", body, expect=KmsUnwrapResult),
        )

    def kms_generate_data_key(
        self, *, key_id: str, key_spec: str | None = None, provider: str | None = None
    ) -> KmsDataKey:
        """``POST /v2/kms/generate-data-key``: a data key, plain (hex) and wrapped."""
        body = compact({"keyId": key_id, "keySpec": key_spec, "provider": provider})
        path = "/v2/kms/generate-data-key"
        return cast(KmsDataKey, self._call("POST", path, body, expect=KmsDataKey))
