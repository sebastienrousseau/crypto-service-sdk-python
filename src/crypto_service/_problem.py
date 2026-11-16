# SPDX-License-Identifier: Apache-2.0 OR MIT
"""RFC 9457 problem parsing: any error body becomes a :class:`Problem`."""

from __future__ import annotations

import json
from typing import Any

from .errors import Problem, ValidationIssue


def _object(content: bytes) -> dict[str, Any] | None:
    try:
        value = json.loads(content)
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _text(body: dict[str, Any], name: str) -> str | None:
    value = body.get(name)
    return value if isinstance(value, str) else None


def _issues(value: object) -> tuple[ValidationIssue, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        ValidationIssue(item["field"], item["message"])
        for item in value
        if isinstance(item, dict)
        and isinstance(item.get("field"), str)
        and isinstance(item.get("message"), str)
    )


def parse_problem(status: int, reason: str, content: bytes) -> Problem:
    """The problem a failed response carries.

    A body that is not JSON, or not a problem (no string ``detail``),
    becomes an ``about:blank`` problem for ``status``. ``status`` is the
    HTTP status of the response, whatever the body claims.
    """
    body = _object(content)
    if body is None or not isinstance(body.get("detail"), str):
        return Problem(
            type="about:blank",
            title=reason or "HTTP error",
            status=status,
            detail=f"The server answered {status} without a problem body",
        )
    return Problem(
        type=_text(body, "type") or "about:blank",
        title=_text(body, "title") or reason or "HTTP error",
        status=status,
        detail=body["detail"],
        instance=_text(body, "instance"),
        code=_text(body, "code"),
        errors=_issues(body.get("errors")),
        raw=body,
    )
