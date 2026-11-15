# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Sign with a server-held Ed25519 key, by keyId, and verify the signature.

The private key never leaves the server: generation returns a keyId and
the public key, and signing takes the keyId.
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
        key = await client.generate_key_pair(algorithm="ed25519", metadata={"use": "sig"})
        print(f"keyId {key['keyId']} public key {key['publicKey']}")
        try:
            signed = await client.sign(key_id=key["keyId"], message="pay 10 EUR to Alice")
            print(f"signature {signed['signature']}")
            checked = await client.verify(
                public_key=key["publicKey"],
                message="pay 10 EUR to Alice",
                signature=signed["signature"],
            )
            tampered = await client.verify(
                public_key=key["publicKey"],
                message="pay 99 EUR to Alice",
                signature=signed["signature"],
            )
            print(f"valid: {checked['valid']}, tampered message valid: {tampered['valid']}")
        finally:
            await client.keys_delete(key_id=key["keyId"])
    return 0 if checked["valid"] and not tampered["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
