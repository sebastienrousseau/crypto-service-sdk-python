# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Hash text with the blocking client.

Run: CRYPTO_SERVICE_URL=http://127.0.0.1:3000 CRYPTO_SERVICE_API_KEY=... python examples/hash.py
"""

from __future__ import annotations

import os
import sys

from crypto_service import Client, RetryOptions


def main() -> int:
    text = sys.argv[1] if len(sys.argv) > 1 else "abc"
    with Client(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        retry=RetryOptions(max_retries=3),
    ) as client:
        for algorithm in ("sha256", "sha3-256", "blake3"):
            result = client.hash(algorithm=algorithm, data=text)
            print(f"{result['algorithm']:>9} {result['digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
