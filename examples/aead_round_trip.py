# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Encrypt and decrypt with XChaCha20-Poly1305 on the server, under a caller-held key.

The key is 32 random bytes from the operating system; the SDK sends it
as hex, as the API asks. The ciphertext comes back as base64.
"""

from __future__ import annotations

import asyncio
import os
import secrets

from crypto_service import AsyncClient, RetryOptions


async def main() -> int:
    key = secrets.token_bytes(32)
    async with AsyncClient(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        retry=RetryOptions(max_retries=3),
    ) as client:
        sealed = await client.encrypt(key=key, plaintext="attack at dawn")
        print(f"{sealed['algorithm']}: {sealed['ciphertext']}")
        opened = await client.decrypt(key=key, ciphertext=sealed["ciphertext"])
        print(f"plaintext: {opened['plaintext']}")
    return 0 if opened["plaintext"] == "attack at dawn" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
