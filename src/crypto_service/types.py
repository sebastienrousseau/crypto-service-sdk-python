# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Request and response shapes of the crypto-server v2 API.

Responses are :class:`~typing.TypedDict` views of the JSON the server
sends, with the API's member names: decoding builds no extra objects,
and a member a newer server adds is still there at runtime. Encodings
follow the OpenAPI document: hex for keys, signatures, digests, MACs,
shared secrets and KEM or HPKE ciphertexts; base64 for AEAD, secretbox,
sealed-box, stream and AES-KW output; UTF-8 text for decrypted
plaintexts.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

HashAlgorithm = Literal["sha256", "sha384", "sha512", "sha3-256", "sha3-512", "blake2b", "blake3"]
HmacAlgorithm = Literal["sha256", "sha384", "sha512", "sha3-256", "sha3-512"]
KdfAlgorithm = Literal["scrypt", "hkdf-sha256", "pbkdf2-sha256"]
KeyAlgorithm = Literal[
    "ed25519", "x25519", "ed448", "x448", "p256", "p384",
    "ml-kem-512", "ml-kem-768", "ml-kem-1024", "ml-dsa-44", "ml-dsa-65", "ml-dsa-87",
]  # fmt: skip
KeyWrapAlgorithm = Literal["aes-kw", "aes-kwp"]
MlDsaLevel = Literal[44, 65, 87]
SlhDsaVariant = Literal[
    "sha2-128f", "sha2-128s", "sha2-192f", "sha2-192s", "sha2-256f", "sha2-256s",
    "shake-128f", "shake-128s", "shake-192f", "shake-192s", "shake-256f", "shake-256s",
]  # fmt: skip
HpkeKem = Literal["x25519", "p256", "x-wing", "x25519-ml-kem-768"]
HpkeAead = Literal["chacha20-poly1305", "aes-128-gcm"]
KmsUsage = Literal["encrypt", "sign", "wrap"]
KmsEncoding = Literal["utf8", "hex"]
OpaqueSuite = Literal["P256-SHA256", "ristretto255-SHA512"]


# --- Requests: nested members ---------------------------------------------


class KeyMetadata(TypedDict, total=False):
    """JOSE-style metadata stored with a server-held key."""

    kid: str
    use: Literal["sig", "enc"]
    exp: str


class KdfParams(TypedDict, total=False):
    """Algorithm parameters of ``/v2/kdf`` (the server enforces floors)."""

    N: int
    r: int
    p: int
    iterations: int
    info: str


class Argon2Params(TypedDict):
    """Argon2id cost parameters, as ``/v2/password/hash`` returns them."""

    t: int
    m: int
    p: int


class StreamSignItem(TypedDict):
    """One message to sign with a server-held key in a batch."""

    id: str
    keyId: str
    message: str


class StreamVerifyItem(TypedDict):
    """One Ed25519 signature to check in a batch (hex key and signature)."""

    id: str
    message: str
    publicKey: str
    signature: str


class MultiRecipient(TypedDict):
    """A recipient of ``/v2/multi-recipient/encrypt`` (hex public keys)."""

    type: Literal["classical", "pq"]
    publicKey: str
    mlKemPublicKey: NotRequired[str]


class StreamRecipient(TypedDict):
    """A recipient of ``/v2/stream/multi-pq-encrypt`` (hex public keys)."""

    recipientId: str
    x25519PublicKey: str
    mlKemPublicKey: str


class TrustedKeys(TypedDict):
    """The keys an ISO 20022 dual signature must verify under (hex)."""

    classicalPublicKey: str
    postQuantumPublicKey: str


# --- Responses -------------------------------------------------------------


class RootInfo(TypedDict):
    """``GET /``: the service description."""

    id: str
    title: str
    description: str
    version: str
    license: str
    url: str
    details: str


class HealthResult(TypedDict):
    """``GET /health``."""

    status: Literal["ok"]
    statusCode: int
    uptime: float


class LiveResult(TypedDict):
    """``GET /live``."""

    status: Literal["alive"]
    uptime: int


class ReadyChecks(TypedDict):
    """The checks behind ``GET /ready``."""

    accepting: bool
    keyStore: bool


class ReadyResult(TypedDict):
    """``GET /ready``."""

    status: Literal["ready", "not_ready"]
    checks: ReadyChecks


class AlgorithmCatalogue(TypedDict):
    """``GET /v2/algorithms``: algorithm names by category."""

    encryption: list[str]
    hashing: list[str]
    kdf: list[str]
    keyExchange: list[str]
    mac: list[str]
    postQuantum: list[str]
    signing: list[str]


class DoraCompliance(TypedDict):
    """``GET /v2/compliance/dora``: the DORA Article 9 and 13 self-assessment."""

    standard: str
    article: str
    status: str
    timestamp: str
    activePrimitivesCount: int
    postQuantumPrimitivesCount: int
    quantumResistanceRatio: float
    cryptographicInventory: list[dict[str, Any]]
    algorithmDeprecationSchedule: list[dict[str, Any]]
    disclaimer: str


class Cbom(TypedDict):
    """``GET /v2/compliance/cbom``: a CycloneDX 1.6 document (not wrapped)."""

    bomFormat: Literal["CycloneDX"]
    specVersion: str
    serialNumber: str
    version: int
    metadata: dict[str, Any]
    components: list[dict[str, Any]]


class AeadResult(TypedDict):
    """``/v2/encrypt``: base64 nonce-prefixed ciphertext."""

    algorithm: str
    ciphertext: str


class PlaintextResult(TypedDict):
    """A UTF-8 plaintext (invalid sequences arrive as U+FFFD)."""

    plaintext: str


class SealedResult(TypedDict):
    """Secretbox or sealed-box output: base64 ``sealed``."""

    algorithm: str
    sealed: str


class PasswordEncryptResult(TypedDict):
    """``/v2/password/encrypt``: the base64 envelope to pass back to decrypt."""

    algorithm: str
    encrypted: str


class KeyWrapResult(TypedDict):
    """``/v2/keys/wrap``: base64 wrapped key."""

    algorithm: str
    wrapped: str


class HashResult(TypedDict):
    """``/v2/hash``: hex digest and its length in bytes."""

    algorithm: str
    digest: str
    length: int


class MacResult(TypedDict):
    """``/v2/hmac``: hex MAC."""

    algorithm: str
    mac: str


class ValidResult(TypedDict):
    """A verification outcome."""

    valid: bool


class AlgorithmValidResult(TypedDict):
    """A verification outcome with the algorithm that checked it."""

    algorithm: str
    valid: bool


class KdfResult(TypedDict):
    """``/v2/kdf``: hex derived key and the hex salt used."""

    algorithm: str
    derivedKey: str
    keyLength: int
    salt: str


class PasswordHashResult(TypedDict):
    """``/v2/password/hash``: Argon2id hash, salt (hex) and PHC string."""

    algorithm: str
    hash: str
    salt: str
    params: Argon2Params
    phc: str


class GeneratedKey(TypedDict):
    """``/v2/keys/generate``: the server-held key's ID and hex public key."""

    keyId: str
    kid: str
    algorithm: str
    publicKey: str
    metadata: KeyMetadata


class ExportedKey(TypedDict):
    """``/v2/keys/export``: the key material, hex; members depend on the algorithm."""

    keyId: str
    algorithm: str
    publicKey: NotRequired[str]
    privateKey: NotRequired[str]
    secretKey: NotRequired[str]
    x25519PublicKey: NotRequired[str]
    x25519PrivateKey: NotRequired[str]
    mlKemPublicKey: NotRequired[str]
    mlKemSecretKey: NotRequired[str]


class DeletedKey(TypedDict):
    """``/v2/keys/delete``."""

    keyId: str
    deleted: bool


class SignatureResult(TypedDict):
    """A hex signature and the algorithm that made it."""

    algorithm: str
    signature: str


class StreamSignResult(TypedDict):
    """``/v2/stream/sign``: one entry per item."""

    count: int
    signatures: list[dict[str, Any]]


class StreamVerifyResult(TypedDict):
    """``/v2/stream/verify``: one result per item."""

    allValid: bool
    count: int
    validCount: int
    results: list[dict[str, Any]]


class KeyPair(TypedDict):
    """A server-held key: its ID and hex public key."""

    algorithm: str
    keyId: str
    publicKey: str


class HybridKeyPair(TypedDict):
    """A server-held X25519 + ML-KEM-768 key: its ID and hex public keys."""

    algorithm: str
    keyId: str
    x25519PublicKey: str
    mlKemPublicKey: str


class KemEncapsulation(TypedDict):
    """``/v2/pq/encapsulate``: hex KEM ciphertext and shared secret."""

    algorithm: str
    ciphertext: str
    sharedSecret: str


class SharedSecret(TypedDict):
    """A decapsulated hex shared secret."""

    algorithm: str
    sharedSecret: str
    combiner: NotRequired[str]


class HybridEncapsulation(TypedDict):
    """``/v2/pq/hybrid/encapsulate``: hex values to send to the key holder."""

    algorithm: str
    combiner: str
    x25519EphemeralPublic: str
    mlKemCiphertext: str
    sharedSecret: str


class Iso20022Result(TypedDict):
    """``/v2/stream/iso20022``: each check of a dual-signed envelope."""

    messageId: str
    valid: bool
    digestMatches: bool
    classicalValid: bool
    postQuantumValid: bool


class StreamEncryptResult(TypedDict):
    """Hybrid STREAM output: base64 ciphertext."""

    algorithm: str
    ciphertext: str


class MultiStreamEncryptResult(TypedDict):
    """Multi-recipient hybrid STREAM output: base64 ciphertext."""

    algorithm: str
    ciphertext: str
    recipientCount: int


class MultiStreamDecryptResult(TypedDict):
    """Multi-recipient STREAM plaintext and the recipient that opened it."""

    plaintext: str
    recipientId: str


class MultiRecipientResult(TypedDict):
    """``/v2/multi-recipient/encrypt``: base64 ciphertext and per-recipient keys."""

    algorithm: str
    ciphertext: str
    recipients: list[dict[str, Any]]


class HpkeSealResult(TypedDict):
    """``/v2/hpke/seal``: hex encapsulated key and ciphertext."""

    encapsulatedKey: str
    ciphertext: str


class DecryptedBytes(TypedDict):
    """A plaintext as UTF-8 text and as hex bytes."""

    plaintext: str
    hex: str


class KmsKey(TypedDict):
    """``/v2/kms/create-key``."""

    keyId: str
    provider: str
    algorithm: str
    usage: str
    enabled: bool
    createdAt: str
    currentVersion: NotRequired[int]


class KmsEncryptResult(TypedDict):
    """``/v2/kms/encrypt``: an opaque provider ciphertext, passed back unchanged."""

    keyId: str
    provider: str
    ciphertext: str
    keyVersion: NotRequired[int]
    context: NotRequired[dict[str, str]]


class KmsDecryptResult(TypedDict):
    """``/v2/kms/decrypt``: the plaintext as UTF-8 text and as hex."""

    keyId: str
    provider: str
    plaintext: str
    hex: str


class KmsWrapResult(TypedDict):
    """``/v2/kms/wrap``: an opaque wrapped key, passed back unchanged."""

    keyId: str
    provider: str
    wrappedKey: str


class KmsUnwrapResult(TypedDict):
    """``/v2/kms/unwrap``: the hex key."""

    keyId: str
    provider: str
    unwrappedKey: str


class KmsDataKey(TypedDict):
    """``/v2/kms/generate-data-key``: hex plaintext key and its wrapped form."""

    keyId: str
    provider: str
    plaintext: str
    ciphertext: str


class OpaqueRegisterInitResult(TypedDict):
    """``/v2/opaque/register/init``: hex registration response."""

    response: str


class OpaqueRegisterFinishResult(TypedDict):
    """``/v2/opaque/register/finish``."""

    credentialIdentifier: str
    status: str


class OpaqueLoginInitResult(TypedDict):
    """``/v2/opaque/login/init``: hex KE2 and the session to finish."""

    ke2: str
    sessionId: str


class OpaqueLoginFinishResult(TypedDict):
    """``/v2/opaque/login/finish``: the hex session key."""

    sessionKey: str
