# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fuzz target bodies, free of atheris so the corpus replays under pytest.

* ``problem``: :func:`crypto_service._problem.parse_problem` on any bytes
  must return a :class:`Problem` with the response's status and never
  raise.
* ``response``: :func:`crypto_service._core.decode_response` on any
  status and bytes, checked against one of a few response types, may
  raise only :class:`ApiError` or :class:`TransportError`.
"""

from __future__ import annotations

from typing import Any

from crypto_service import ApiError, TransportError, _core, types
from crypto_service._problem import parse_problem

#: The types the response target checks against: nothing, scalars,
#: Literal and nested members, NotRequired members, lists and mappings.
EXPECTED: tuple[object, ...] = (
    Any,
    str,
    types.HashResult,
    types.ReadyResult,
    types.SharedSecret,
    types.StreamSignResult,
    types.KmsEncryptResult,
    types.Cbom,
)


def _status(data: bytes, low: int, span: int) -> tuple[int, bytes]:
    head = int.from_bytes(data[:2], "big") if data else 0
    return low + head % span, data[2:]


def _require(condition: bool, what: str) -> None:
    if not condition:
        raise AssertionError(what)


def problem(data: bytes) -> None:
    status, body = _status(data, 400, 200)
    result = parse_problem(status, "Reason", body)
    _require(result.status == status, "status changed")
    _require(isinstance(result.detail, str), "detail is not text")
    _require(all(isinstance(i.message, str) for i in result.errors), "message is not text")


def response(data: bytes) -> None:
    status, body = _status(data, 200, 400)
    wrapped = bool(data[:1]) and data[0] & 1 == 1
    expected = EXPECTED[data[1] % len(EXPECTED)] if len(data) > 1 else Any
    try:
        _core.decode_response(status, "Reason", body, wrapped=wrapped, expected=expected)
    except ApiError as error:
        _require(error.status == status >= 400, "ApiError for the wrong status")
    except TransportError:
        pass
