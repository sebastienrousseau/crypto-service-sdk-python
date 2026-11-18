# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Checks that a decoded success response has the types the API documents.

The typed methods return :mod:`crypto_service.types` views of the JSON
the server sent. Before one is returned, :func:`check_shape` walks it
against the declared type: every required member present, every member
present with its JSON type, a ``Literal`` one of its values, every list
item and mapping value checked in turn. Members the type does not
declare are kept, so a newer server can add some. A mismatch raises
:class:`~crypto_service.TransportError` naming the member, never its
value.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any, Literal, NotRequired, Required, get_args, get_origin, get_type_hints
from typing import is_typeddict as _is_typeddict

from .errors import TransportError

_SCALARS: dict[object, Callable[[object], bool]] = {
    str: lambda value: isinstance(value, str),
    bool: lambda value: isinstance(value, bool),
    int: lambda value: isinstance(value, int) and not isinstance(value, bool),
    float: lambda value: isinstance(value, int | float) and not isinstance(value, bool),
}


def check_shape(value: Any, expected: Any, where: str = "data") -> Any:
    """``value``, once checked against ``expected``; raises ``TransportError`` otherwise."""
    _check(value, expected, where)
    return value


def _fail(where: str) -> None:
    raise TransportError(f"The server's response does not match the API at {where}")


def _check(value: Any, expected: Any, where: str) -> None:
    if expected is Any:
        return
    if _is_typeddict(expected):
        _check_members(value, expected, where)
        return
    origin = get_origin(expected)
    if origin is list:
        _check_items(value, get_args(expected)[0], where)
    elif origin is dict:
        _check_values(value, get_args(expected)[1], where)
    elif origin is Literal:
        if not any(type(value) is type(arg) and value == arg for arg in get_args(expected)):
            _fail(where)
    elif not _SCALARS[expected](value):
        _fail(where)


def _check_members(value: Any, expected: type, where: str) -> None:
    if not isinstance(value, dict):
        _fail(where)
    for name, (member, required) in _members(expected).items():
        if name in value:
            _check(value[name], member, f"{where}.{name}")
        elif required:
            _fail(f"{where}.{name}")


def _check_items(value: Any, item: Any, where: str) -> None:
    if not isinstance(value, list):
        _fail(where)
    for index, element in enumerate(value):
        _check(element, item, f"{where}[{index}]")


def _check_values(value: Any, member: Any, where: str) -> None:
    if not isinstance(value, dict):
        _fail(where)
    for name, element in value.items():
        _check(element, member, f"{where}.{name}")


@functools.cache
def _members(expected: type) -> dict[str, tuple[Any, bool]]:
    """Each member of a TypedDict: its type and whether it is required.

    Read from the annotations rather than ``__required_keys__``, which
    counts a ``NotRequired`` member as required when the annotations are
    strings (``from __future__ import annotations``, as in ``types``).
    """
    total = getattr(expected, "__total__", True)
    members: dict[str, tuple[Any, bool]] = {}
    for name, hint in get_type_hints(expected, include_extras=True).items():
        qualifier = get_origin(hint)
        if qualifier in (Required, NotRequired):
            members[name] = (get_args(hint)[0], qualifier is Required)
        else:
            members[name] = (hint, total)
    return members
