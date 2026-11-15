<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Comparison

How this SDK relates to the other ways of calling crypto-server from
Python and to the other Crypto Service SDKs. Facts only; where a cell is
not known, it says so.

| | crypto-service-sdk-python | Raw `httpx` / `requests` | A client generated from the OpenAPI document |
| :--- | :--- | :--- | :--- |
| Coverage of v2 | 59 of 59 operations, typed | Whatever you write | Depends on the generator |
| Conformance kit in CI | Yes, against a live server | No | No |
| Async and blocking | Both, from one source | Both (httpx) | Depends on the generator |
| Retry-safety table | Yes (stateful operations not repeated after 504 or a lost connection) | No | No |
| RFC 9457 problems as typed exceptions | Yes | No | Partly |
| Encodings | `bytes` encoded as the API names; responses unchanged | Manual | Strings |
| Redirects | Refused | Followed by `requests`, not by httpx | Depends |

## Across the suite

Every Crypto Service SDK implements the same contract
([crypto-service `docs/sdk-contract.md`](https://github.com/sebastienrousseau/crypto-service/blob/main/docs/sdk-contract.md)):
the same options, retry table, error model, User-Agent pattern and
benchmark scenario names, and each runs the same kit.

| SDK | Async model | Registry |
| :--- | :--- | :--- |
| `@sebastienrousseau/crypto-sdk` | Promise | npm |
| crypto-service-sdk-java | CompletableFuture | Maven Central |
| crypto-service-sdk-rust | tokio (optional blocking) | crates.io |
| crypto-service-sdk-go | context.Context | Go module proxy |
| crypto-service-sdk-cpp | std::future and blocking | GitHub release (CMake package) |
| crypto-service-sdk-dotnet | Task, CancellationToken | NuGet |
| **crypto-service-sdk-python** | **asyncio and blocking** | **PyPI** |
