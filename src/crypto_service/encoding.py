# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Conversions between ``bytes`` and the encodings the API names.

The API carries binary values as lowercase hex (keys, signatures,
digests, MACs, shared secrets, KEM ciphertexts, HPKE output) or as
standard padded base64 (AEAD, secretbox, sealed-box, stream,
password-encryption and AES-KW output). Methods accept ``bytes`` where
the API takes one of these and encode them here; responses keep the
API's strings, and :func:`from_hex` and :func:`from_base64` turn them
into ``bytes``.
"""

from __future__ import annotations

import base64
import binascii

Hex = str | bytes
"""A hex field: ``bytes`` are hex-encoded, a ``str`` is sent as it is."""

Base64 = str | bytes
"""A base64 field: ``bytes`` are base64-encoded, a ``str`` is sent as it is."""


def to_hex(value: Hex) -> str:
    """``bytes`` as lowercase hex; a ``str`` unchanged."""
    return value.hex() if isinstance(value, bytes) else value


def to_base64(value: Base64) -> str:
    """``bytes`` as standard padded base64; a ``str`` unchanged."""
    return base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else value


def from_hex(value: str) -> bytes:
    """Decode an API hex string; raises ``ValueError`` when it is not hex."""
    return bytes.fromhex(value)


def from_base64(value: str) -> bytes:
    """Decode an API base64 string; raises ``ValueError`` when it is not base64."""
    try:
        return base64.b64decode(value, validate=True)
    except binascii.Error as exc:
        raise ValueError("not standard padded base64") from exc
