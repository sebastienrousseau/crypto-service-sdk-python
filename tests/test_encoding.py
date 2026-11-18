# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Encoding helpers: bytes to the API's hex and base64, and back."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from crypto_service.encoding import from_base64, from_hex, to_base64, to_hex


def test_strings_pass_through() -> None:
    assert to_hex("ABcd") == "ABcd"
    assert to_base64("not checked") == "not checked"


def test_known_values() -> None:
    assert to_hex(b"\x00\xff") == "00ff"
    assert to_base64(b"\xff") == "/w=="
    assert from_hex("00FF") == b"\x00\xff"
    assert from_base64("/w==") == b"\xff"


def test_invalid_input_raises_value_error() -> None:
    with pytest.raises(ValueError, match="hexadecimal"):
        from_hex("zz")
    with pytest.raises(ValueError, match="base64"):
        from_base64("!!")


@given(st.binary())
def test_round_trips(value: bytes) -> None:
    assert from_hex(to_hex(value)) == value
    assert from_base64(to_base64(value)) == value
    assert to_hex(value) == to_hex(value).lower()
