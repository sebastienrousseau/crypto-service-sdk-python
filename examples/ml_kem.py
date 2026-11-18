# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""ML-KEM-768: encapsulate to a server-held key's public key, decapsulate by keyId.

Both sides arrive at the same shared secret; the decapsulation key stays
on the server.
"""

from __future__ import annotations

import asyncio
import os

from crypto_service import AsyncClient, RetryOptions


async def main() -> int:
    async with AsyncClient(
        os.environ["CRYPTO_SERVICE_URL"],
        api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
        retry=RetryOptions(max_retries=3),
    ) as client:
        key = await client.ml_kem_generate_key_pair()
        print(f"{key['algorithm']} keyId {key['keyId']}")
        try:
            sent = await client.ml_kem_encapsulate(public_key=key["publicKey"])
            received = await client.ml_kem_decapsulate(
                key_id=key["keyId"], ciphertext=sent["ciphertext"]
            )
            print(f"ciphertext {len(sent['ciphertext']) // 2} bytes")
            same = sent["sharedSecret"] == received["sharedSecret"]
            print(f"shared secrets match: {same}")
        finally:
            await client.keys_delete(key_id=key["keyId"])
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
