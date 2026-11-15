# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The conformance kit: integrity always, the vectors against a live server.

The live part needs ``CRYPTO_SERVICE_URL``, ``CRYPTO_SERVICE_API_KEY``
and ``CRYPTO_SERVICE_JWT_SECRET`` (the server's ``JWT_SECRET``; the kit
needs tokens with chosen scopes). Without them it skips, unless
``CRYPTO_SERVICE_REQUIRE_LIVE=1`` (set by ``make conformance``), when it
fails.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from .operations import OPS
from .support.kit import checksum_mismatches, kit_files
from .support.runner import ROUTES, FileResult, LiveServer, run_file

FILES = kit_files()
RESULTS: list[FileResult] = []
_ENV = ("CRYPTO_SERVICE_URL", "CRYPTO_SERVICE_API_KEY", "CRYPTO_SERVICE_JWT_SECRET")


def test_kit_matches_its_checksums() -> None:
    assert checksum_mismatches() == []


def test_every_kit_route_has_a_typed_method() -> None:
    kit_routes = {
        (v["request"]["method"], v["request"]["path"])
        for _, document in FILES
        for v in document["vectors"]
        if not v["request"]["path"].startswith("/v1/")
    }
    excluded = {("GET", "/metrics"), ("GET", "/v2/no-such-route")}
    assert kit_routes - excluded == set(ROUTES)
    assert len({op.path for op in OPS if op.path.startswith("/v2/")}) == 59


def live_server() -> LiveServer:
    missing = [name for name in _ENV if not os.environ.get(name)]
    if missing:
        message = "set " + ", ".join(missing) + " to run the kit against a server"
        if os.environ.get("CRYPTO_SERVICE_REQUIRE_LIVE") == "1":
            pytest.fail(message)
        pytest.skip(message)
    return LiveServer(
        url=os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        jwt_secret=os.environ["CRYPTO_SERVICE_JWT_SECRET"],
        issuer=os.environ.get("CRYPTO_SERVICE_JWT_ISSUER"),
        audience=os.environ.get("CRYPTO_SERVICE_JWT_AUDIENCE"),
    )


@pytest.mark.conformance
@pytest.mark.parametrize(("name", "document"), FILES, ids=[name for name, _ in FILES])
async def test_vector_file(name: str, document: dict[str, Any]) -> None:
    result = await run_file(live_server(), name, document)
    RESULTS.append(result)
    assert result.failed == []
