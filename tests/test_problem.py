# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Problem parsing: every error body becomes a problem, and nothing raises."""

from __future__ import annotations

import json

from hypothesis import given
from hypothesis import strategies as st

from crypto_service._problem import parse_problem
from crypto_service.errors import ValidationIssue

VALIDATION = {
    "type": "urn:crypto-service:problem:validation-failed",
    "title": "Validation failed",
    "status": 400,
    "detail": "body must have required property 'data'",
    "instance": "/v2/hash",
    "errors": [
        {"field": "/data", "message": "is required"},
        {"field": 1, "message": "dropped"},
        "dropped",
    ],
}


def test_full_problem() -> None:
    problem = parse_problem(400, "Bad Request", json.dumps(VALIDATION).encode())
    assert problem.type.endswith("validation-failed")
    assert problem.title == "Validation failed"
    assert problem.status == 400
    assert problem.instance == "/v2/hash"
    assert problem.code is None
    assert problem.errors == (ValidationIssue("/data", "is required"),)
    assert problem.raw == VALIDATION
    assert "required" not in repr(problem)


def test_minimal_problem_defaults() -> None:
    problem = parse_problem(409, "Conflict", b'{"detail": "d", "errors": {}}')
    assert problem.type == "about:blank"
    assert problem.title == "Conflict"
    assert problem.errors == ()
    assert parse_problem(409, "", b'{"detail": "d"}').title == "HTTP error"


def test_status_comes_from_the_response() -> None:
    assert parse_problem(503, "", b'{"detail": "d", "status": 200}').status == 503


def test_non_problems_become_about_blank() -> None:
    for body in (b"", b"<html/>", b"[]", b'{"title": "no detail"}', b'{"detail": 5}'):
        problem = parse_problem(502, "Bad Gateway", body)
        assert problem.type == "about:blank"
        assert problem.title == "Bad Gateway"
        assert problem.detail == "The server answered 502 without a problem body"
        assert problem.raw == {}


@given(st.integers(min_value=400, max_value=599), st.text(), st.binary())
def test_never_raises_on_bytes(status: int, reason: str, body: bytes) -> None:
    assert parse_problem(status, reason, body).status == status


json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda inner: st.lists(inner) | st.dictionaries(st.text(), inner),
)


@given(st.dictionaries(st.sampled_from(["type", "title", "detail", "errors", "code"]), json_values))
def test_never_raises_on_json(body: dict[str, object]) -> None:
    problem = parse_problem(400, "Bad Request", json.dumps(body).encode())
    assert isinstance(problem.detail, str)
    assert all(isinstance(issue.field, str) for issue in problem.errors)
