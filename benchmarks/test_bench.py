# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Benchmarks, with the scenario names every Crypto Service SDK uses.

``encode_request``, ``decode_response`` and ``decode_problem`` measure
the client's own work, no network. ``round_trip_hash`` is a loopback
round trip to the server at ``CRYPTO_SERVICE_URL`` and skips without
one. Nothing is asserted about speed: ``make bench`` writes the numbers
for docs/BENCHMARKS.md, and CI only smoke-runs them.

The responses in ``benchmarks/responses/`` were recorded from
crypto-server at the commit in ``ci/server.ref``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from crypto_service import Client, RetryOptions, _core
from crypto_service._problem import parse_problem

RESPONSES = Path(__file__).parent / "responses"
CONFIG = _core.Config.create(
    "http://127.0.0.1:3000",
    api_key="synthetic-benchmark-key",
    token=None,
    timeout=30.0,
    deadline=None,
    retry=None,
    traceparent=None,
)


def test_encode_request(benchmark: Any) -> None:
    benchmark.group = "encode_request"

    def encode() -> tuple[bytes, dict[str, str]]:
        body = {"algorithm": "sha256", "data": "abc"}
        return _core.encode_body(body), CONFIG.headers(auth=True, has_body=True)

    content, headers = benchmark(encode)
    assert content
    assert headers


def test_decode_response(benchmark: Any) -> None:
    benchmark.group = "decode_response"
    content = (RESPONSES / "hash.json").read_bytes()
    value = benchmark(_core.decode_response, 200, "OK", content, wrapped=True)
    assert value["algorithm"] == "sha256"


def test_decode_problem(benchmark: Any) -> None:
    benchmark.group = "decode_problem"
    content = (RESPONSES / "problem.json").read_bytes()
    problem = benchmark(parse_problem, 400, "Bad Request", content)
    assert problem.errors


@pytest.mark.skipif(not os.environ.get("CRYPTO_SERVICE_URL"), reason="needs CRYPTO_SERVICE_URL")
def test_round_trip_hash(benchmark: Any) -> None:
    benchmark.group = "round_trip_hash"
    rounds = int(os.environ.get("CRYPTO_SERVICE_BENCH_ROUNDS", "20"))
    with Client(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ.get("CRYPTO_SERVICE_API_KEY"),
        retry=RetryOptions(max_retries=5),
    ) as client:
        client.health()  # open the connection before timing
        result = benchmark.pedantic(
            client.hash, kwargs={"algorithm": "sha256", "data": "abc"}, rounds=rounds
        )
    assert result["length"] == 32
