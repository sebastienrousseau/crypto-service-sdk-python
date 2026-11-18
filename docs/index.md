<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Crypto Service SDK for Python

A typed async and blocking Python client for the Crypto Service REST API
(crypto-server v2). The SDK implements no cryptography: every operation
is one HTTP call to a crypto-server you run.

```python
import asyncio

from crypto_service import AsyncClient


async def main() -> None:
    async with AsyncClient("http://127.0.0.1:3000", api_key="...") as client:
        print(await client.hash(algorithm="sha256", data="abc"))


asyncio.run(main())
```

- [Architecture](ARCHITECTURE.md): how a call travels through the SDK.
- [Decision records](adr/README.md): why it is built this way.
- [Comparison](COMPARISON.md), [Benchmarks](BENCHMARKS.md),
  [Policies](POLICIES.md), [Roadmap](ROADMAP.md).
- [Release 0.0.40](releases/0.0.40.md).
