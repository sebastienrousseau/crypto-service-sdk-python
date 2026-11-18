# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Many requests at once with the async client: one pool, shared by every task.

The server meters each principal (60 requests a minute by default), so
the client retries 429 answers, waiting as long as Retry-After asks.
"""

from __future__ import annotations

import asyncio
import os
import time

from crypto_service import AsyncClient, RetryOptions


async def main() -> int:
    messages = [f"message {n}" for n in range(16)]
    async with AsyncClient(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        retry=RetryOptions(max_retries=5),
        deadline=60.0,
    ) as client:
        started = time.perf_counter()
        results = await asyncio.gather(
            *(client.hash(algorithm="sha256", data=message) for message in messages)
        )
        elapsed = time.perf_counter() - started
    for message, result in zip(messages, results, strict=True):
        print(f"{message:>11}: {result['digest'][:16]}...")
    print(f"{len(results)} hashes in {elapsed:.3f} s over one connection pool")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
