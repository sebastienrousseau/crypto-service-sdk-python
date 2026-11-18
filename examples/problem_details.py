# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Handle errors: RFC 9457 problem details, validation errors, transport errors."""

from __future__ import annotations

import asyncio
import os

from crypto_service import ApiError, AsyncClient, RetryOptions, TransportError


async def main() -> int:
    async with AsyncClient(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        retry=RetryOptions(max_retries=3),
    ) as client:
        try:
            await client.sign(key_id="k_AAAAAAAAAAAAAAAAAAAAAA", message="m")
        except ApiError as error:
            problem = error.problem
            print(f"{error.status} {problem.type} code={problem.code}")
            print(f"  detail: {problem.detail}")

        try:
            await client.hash(algorithm="md5", data="abc")  # type: ignore[arg-type]
        except ApiError as error:
            print(f"{error.status} {error.problem.title}")
            for issue in error.problem.errors:
                print(f"  {issue.field}: {issue.message}")

        response = await client.request("POST", "/v2/hash", body={"algorithm": "sha256"})
        print(f"raw request: {response.status} {response.media_type}")

    # Nothing listens on port 9 (discard) here: no response at all.
    async with AsyncClient("http://127.0.0.1:9", timeout=2.0) as offline:
        try:
            await offline.health()
        except TransportError as error:
            print(f"transport error: {error} (timed out: {error.timed_out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
