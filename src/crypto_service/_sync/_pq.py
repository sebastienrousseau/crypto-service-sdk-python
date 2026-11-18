# SPDX-License-Identifier: Apache-2.0 OR MIT
# Generated from src/crypto_service/_async/_pq.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
"""Post-quantum KEMs (ML-KEM, hybrid X25519 + ML-KEM) and signatures (ML-DSA, SLH-DSA)."""

from __future__ import annotations

from typing import Any, cast

from ..encoding import Hex, to_hex
from ..types import (
    AlgorithmValidResult,
    HybridEncapsulation,
    HybridKeyPair,
    Iso20022Result,
    KemEncapsulation,
    KeyPair,
    MlDsaLevel,
    SharedSecret,
    SignatureResult,
    SlhDsaVariant,
    TrustedKeys,
)
from ._base import Base


class PqOps(Base):
    """Post-quantum routes. Key generation is stateful (see the retry table)."""

    def ml_kem_generate_key_pair(self) -> KeyPair:
        """``POST /v2/pq/keygen``: a server-held ML-KEM-768 key pair."""
        return cast(KeyPair, self._call("POST", "/v2/pq/keygen", {}, expect=KeyPair))

    def ml_kem_encapsulate(self, *, public_key: Hex) -> KemEncapsulation:
        """``POST /v2/pq/encapsulate``: a shared secret for an ML-KEM-768 public key."""
        body = {"publicKey": to_hex(public_key)}
        return cast(
            KemEncapsulation,
            self._call("POST", "/v2/pq/encapsulate", body, expect=KemEncapsulation),
        )

    def ml_kem_decapsulate(self, *, key_id: str, ciphertext: Hex) -> SharedSecret:
        """``POST /v2/pq/decapsulate``: recover the shared secret with a server-held key."""
        body = {"keyId": key_id, "ciphertext": to_hex(ciphertext)}
        return cast(
            SharedSecret, self._call("POST", "/v2/pq/decapsulate", body, expect=SharedSecret)
        )

    def pq_generate_key_pair(self) -> HybridKeyPair:
        """``POST /v2/pq/hybrid/keygen``: a server-held X25519 + ML-KEM-768 key pair."""
        return cast(
            HybridKeyPair,
            self._call("POST", "/v2/pq/hybrid/keygen", {}, expect=HybridKeyPair),
        )

    def pq_encapsulate(
        self, *, x25519_public_key: Hex, ml_kem_public_key: Hex
    ) -> HybridEncapsulation:
        """``POST /v2/pq/hybrid/encapsulate``: a hybrid shared secret."""
        body = {
            "x25519PublicKey": to_hex(x25519_public_key),
            "mlKemPublicKey": to_hex(ml_kem_public_key),
        }
        return cast(
            HybridEncapsulation,
            self._call("POST", "/v2/pq/hybrid/encapsulate", body, expect=HybridEncapsulation),
        )

    def pq_decapsulate(
        self, *, key_id: str, x25519_ephemeral_public: Hex, ml_kem_ciphertext: Hex
    ) -> SharedSecret:
        """``POST /v2/pq/hybrid/decapsulate``: recover a hybrid shared secret."""
        body = {
            "keyId": key_id,
            "x25519EphemeralPublic": to_hex(x25519_ephemeral_public),
            "mlKemCiphertext": to_hex(ml_kem_ciphertext),
        }
        return cast(
            SharedSecret,
            self._call("POST", "/v2/pq/hybrid/decapsulate", body, expect=SharedSecret),
        )

    def pq_sign_keygen(self, *, level: MlDsaLevel) -> KeyPair:
        """``POST /v2/pq/dsa/keygen``: a server-held ML-DSA key pair (FIPS 204)."""
        return cast(
            KeyPair, self._call("POST", "/v2/pq/dsa/keygen", {"level": level}, expect=KeyPair)
        )

    def pq_sign(self, *, key_id: str, message: str) -> SignatureResult:
        """``POST /v2/pq/dsa/sign``: sign with a server-held ML-DSA key."""
        body = {"keyId": key_id, "message": message}
        return cast(
            SignatureResult,
            self._call("POST", "/v2/pq/dsa/sign", body, expect=SignatureResult),
        )

    def pq_verify(
        self, *, level: MlDsaLevel, public_key: Hex, message: str, signature: Hex
    ) -> AlgorithmValidResult:
        """``POST /v2/pq/dsa/verify``: check an ML-DSA signature."""
        body = {
            "level": level,
            "publicKey": to_hex(public_key),
            "message": message,
            "signature": to_hex(signature),
        }
        return cast(
            AlgorithmValidResult,
            self._call("POST", "/v2/pq/dsa/verify", body, expect=AlgorithmValidResult),
        )

    def pq_hash_sign_keygen(self, *, variant: SlhDsaVariant) -> KeyPair:
        """``POST /v2/pq/slh-dsa/keygen``: a server-held SLH-DSA key pair (FIPS 205)."""
        body = {"variant": variant}
        return cast(KeyPair, self._call("POST", "/v2/pq/slh-dsa/keygen", body, expect=KeyPair))

    def pq_hash_sign(self, *, key_id: str, message: str) -> SignatureResult:
        """``POST /v2/pq/slh-dsa/sign``: sign with a server-held SLH-DSA key."""
        body = {"keyId": key_id, "message": message}
        return cast(
            SignatureResult,
            self._call("POST", "/v2/pq/slh-dsa/sign", body, expect=SignatureResult),
        )

    def pq_hash_verify(
        self, *, variant: SlhDsaVariant, public_key: Hex, message: str, signature: Hex
    ) -> AlgorithmValidResult:
        """``POST /v2/pq/slh-dsa/verify``: check an SLH-DSA signature."""
        body = {
            "variant": variant,
            "publicKey": to_hex(public_key),
            "message": message,
            "signature": to_hex(signature),
        }
        return cast(
            AlgorithmValidResult,
            self._call("POST", "/v2/pq/slh-dsa/verify", body, expect=AlgorithmValidResult),
        )

    def stream_iso20022(
        self, *, envelope: dict[str, Any], payload: Any, trusted_keys: TrustedKeys
    ) -> Iso20022Result:
        """``POST /v2/stream/iso20022``: verify an Ed25519 + ML-DSA dual-signed envelope.

        ``envelope`` is the signed envelope as the signer produced it;
        ``payload`` is the message it covers (any JSON value).
        """
        body = {"envelope": envelope, "payload": payload, "trustedKeys": trusted_keys}
        return cast(
            Iso20022Result,
            self._call("POST", "/v2/stream/iso20022", body, expect=Iso20022Result),
        )
