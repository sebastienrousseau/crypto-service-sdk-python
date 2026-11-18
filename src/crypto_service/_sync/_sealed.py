# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
# Generated from src/crypto_service/_async/_sealed.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Public-key encryption: sealed boxes, HPKE, hybrid STREAM and multi-recipient."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from .._core import compact
from ..encoding import Base64, Hex, to_base64, to_hex
from ..types import (
    DecryptedBytes,
    HpkeAead,
    HpkeKem,
    HpkeSealResult,
    KeyPair,
    MultiRecipient,
    MultiRecipientResult,
    MultiStreamDecryptResult,
    MultiStreamEncryptResult,
    PlaintextResult,
    SealedResult,
    StreamEncryptResult,
    StreamRecipient,
)
from ._base import Base


def _hpke_text(value: Hex | None) -> str | None:
    """HPKE text members: the server reads even-length hex as bytes."""
    return None if value is None else to_hex(value)


class SealedOps(Base):
    """Encryption to a public key; opening uses a server-held ``keyId``."""

    def sealedbox_seal(self, *, recipient_public_key: Hex, plaintext: str) -> SealedResult:
        """``POST /v2/sealedbox/seal``: anonymous encryption to an X25519 public key."""
        body = {"recipientPublicKey": to_hex(recipient_public_key), "plaintext": plaintext}
        return cast(
            SealedResult, self._call("POST", "/v2/sealedbox/seal", body, expect=SealedResult)
        )

    def sealedbox_open(self, *, key_id: str, sealed: Base64) -> str:
        """``POST /v2/sealedbox/open``: the plaintext (``data`` is a bare string)."""
        body = {"keyId": key_id, "sealed": to_base64(sealed)}
        return cast(str, self._call("POST", "/v2/sealedbox/open", body, expect=str))

    def sealedbox_seal_pq(
        self, *, x25519_public_key: Hex, ml_kem_public_key: Hex, plaintext: str
    ) -> SealedResult:
        """``POST /v2/sealedbox/seal-pq``: seal to an X25519 + ML-KEM-768 key pair."""
        body = {
            "x25519PublicKey": to_hex(x25519_public_key),
            "mlKemPublicKey": to_hex(ml_kem_public_key),
            "plaintext": plaintext,
        }
        return cast(
            SealedResult,
            self._call("POST", "/v2/sealedbox/seal-pq", body, expect=SealedResult),
        )

    def sealedbox_open_pq(self, *, key_id: str, sealed: Base64) -> str:
        """``POST /v2/sealedbox/open-pq``: the plaintext (``data`` is a bare string)."""
        body = {"keyId": key_id, "sealed": to_base64(sealed)}
        return cast(str, self._call("POST", "/v2/sealedbox/open-pq", body, expect=str))

    def stream_pq_encrypt(
        self,
        *,
        x25519_public_key: Hex,
        ml_kem_public_key: Hex,
        plaintext: str,
        chunk_size: int | None = None,
    ) -> StreamEncryptResult:
        """``POST /v2/stream/pq-encrypt``: hybrid STREAM AEAD to one recipient."""
        body = compact(
            {
                "x25519PublicKey": to_hex(x25519_public_key),
                "mlKemPublicKey": to_hex(ml_kem_public_key),
                "plaintext": plaintext,
                "chunkSize": chunk_size,
            }
        )
        return cast(
            StreamEncryptResult,
            self._call("POST", "/v2/stream/pq-encrypt", body, expect=StreamEncryptResult),
        )

    def stream_pq_decrypt(
        self, *, key_id: str, ciphertext: Base64, chunk_size: int | None = None
    ) -> PlaintextResult:
        """``POST /v2/stream/pq-decrypt``: open hybrid STREAM ciphertext."""
        body = compact(
            {"keyId": key_id, "ciphertext": to_base64(ciphertext), "chunkSize": chunk_size}
        )
        return cast(
            PlaintextResult,
            self._call("POST", "/v2/stream/pq-decrypt", body, expect=PlaintextResult),
        )

    def stream_multi_pq_encrypt(
        self,
        *,
        recipients: Sequence[StreamRecipient],
        plaintext: str,
        chunk_size: int | None = None,
    ) -> MultiStreamEncryptResult:
        """``POST /v2/stream/multi-pq-encrypt``: hybrid STREAM to several recipients."""
        body = compact(
            {"recipients": list(recipients), "plaintext": plaintext, "chunkSize": chunk_size}
        )
        path = "/v2/stream/multi-pq-encrypt"
        return cast(
            MultiStreamEncryptResult,
            self._call("POST", path, body, expect=MultiStreamEncryptResult),
        )

    def stream_multi_pq_decrypt(
        self,
        *,
        key_id: str,
        ciphertext: Base64,
        recipient_id: str | None = None,
        chunk_size: int | None = None,
    ) -> MultiStreamDecryptResult:
        """``POST /v2/stream/multi-pq-decrypt``: open it as one of the recipients."""
        body = compact(
            {
                "keyId": key_id,
                "ciphertext": to_base64(ciphertext),
                "recipientId": recipient_id,
                "chunkSize": chunk_size,
            }
        )
        path = "/v2/stream/multi-pq-decrypt"
        return cast(
            MultiStreamDecryptResult,
            self._call("POST", path, body, expect=MultiStreamDecryptResult),
        )

    def multi_recipient_encrypt(
        self, *, plaintext: str, recipients: Sequence[MultiRecipient]
    ) -> MultiRecipientResult:
        """``POST /v2/multi-recipient/encrypt``: one ciphertext, classical and PQ recipients."""
        body = {"plaintext": plaintext, "recipients": list(recipients)}
        path = "/v2/multi-recipient/encrypt"
        return cast(
            MultiRecipientResult, self._call("POST", path, body, expect=MultiRecipientResult)
        )

    def hpke_generate_key_pair(self, *, kem: HpkeKem | None = None) -> KeyPair:
        """``POST /v2/hpke/keygen``: a server-held HPKE key (X-Wing by default)."""
        return cast(
            KeyPair,
            self._call("POST", "/v2/hpke/keygen", compact({"kem": kem}), expect=KeyPair),
        )

    def hpke_seal(
        self,
        *,
        recipient_public_key: Hex,
        plaintext: Hex,
        kem: HpkeKem | None = None,
        aead: HpkeAead | None = None,
        info: Hex | None = None,
        aad: Hex | None = None,
        psk: Hex | None = None,
        psk_id: Hex | None = None,
    ) -> HpkeSealResult:
        """``POST /v2/hpke/seal``: RFC 9180 single-shot encryption.

        The server reads ``plaintext``, ``info`` and ``aad`` as hex when
        they are an even-length hex string and as UTF-8 text otherwise.
        ``bytes`` are sent as hex, so they always arrive as those bytes;
        a ``str`` is sent unchanged and is read by that rule.
        """
        body = compact(
            {
                "recipientPublicKey": to_hex(recipient_public_key),
                "plaintext": to_hex(plaintext),
                "kem": kem,
                "aead": aead,
                "info": _hpke_text(info),
                "aad": _hpke_text(aad),
                "psk": _hpke_text(psk),
                "pskId": _hpke_text(psk_id),
            }
        )
        return cast(
            HpkeSealResult, self._call("POST", "/v2/hpke/seal", body, expect=HpkeSealResult)
        )

    def hpke_open(
        self,
        *,
        key_id: str,
        encapsulated_key: Hex,
        ciphertext: Hex,
        aead: HpkeAead | None = None,
        info: Hex | None = None,
        aad: Hex | None = None,
        psk: Hex | None = None,
        psk_id: Hex | None = None,
    ) -> DecryptedBytes:
        """``POST /v2/hpke/open``: the plaintext as UTF-8 text and as hex."""
        body = compact(
            {
                "keyId": key_id,
                "encapsulatedKey": to_hex(encapsulated_key),
                "ciphertext": to_hex(ciphertext),
                "aead": aead,
                "info": _hpke_text(info),
                "aad": _hpke_text(aad),
                "psk": _hpke_text(psk),
                "pskId": _hpke_text(psk_id),
            }
        )
        return cast(
            DecryptedBytes, self._call("POST", "/v2/hpke/open", body, expect=DecryptedBytes)
        )
