<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

<p align="center">
  <img src="https://cloudcdn.pro/crypto-service/v1/logos/crypto-service.svg" alt="Crypto Service logo" width="128" />
</p>

<h1 align="center">Crypto Service SDK for Python</h1>

<p align="center">
  A typed async and blocking Python client for the Crypto Service REST API: hashing, AEAD, server-held Ed25519, ML-KEM, ML-DSA, SLH-DSA, HPKE and KMS keys, with no cryptography in the client.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/crypto-service-sdk-python/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/crypto-service-sdk-python/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/crypto-service-sdk-python/"><img src="https://img.shields.io/pypi/v/crypto-service-sdk-python?style=for-the-badge&color=fc8d62&logo=pypi&logoColor=white" alt="PyPI" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/crypto-service-sdk-python/tree/main/docs"><img src="https://img.shields.io/badge/docs-manual-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/crypto-service-sdk-python"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/crypto-service-sdk-python?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE-APACHE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/crypto-service-sdk-python/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.11%2B-3776ab.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11 or newer" height="28" /></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/sebastienrousseau/crypto-service-sdk-python/main/.github/demo.gif" alt="The Python examples against a local crypto-server: SHA-256, SHA3-256 and BLAKE3 digests of the same text, then an Ed25519 signature made with a server-held key and checked, valid for the signed message and invalid for a changed one" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install): from PyPI with pip or uv
- [Requirements](#requirements): Python floor, platforms, the server
- [Quick Start](#quick-start): hash text and sign with a server-held key

**The Crypto Service ecosystem**

- [The Crypto Service ecosystem](#the-crypto-service-ecosystem): crypto-server, its SDKs and the shared conformance kit

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance): the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison): short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks): the scenarios and how to run them; [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features): module-level capability list
- [Configuration](#configuration): client options
- [Examples](#examples): runnable example index

**Operational**

- [When not to use Crypto Service](#when-not-to-use-crypto-service): limitations
- [Development](#development): make targets, conformance, CI
- [Security](#security): guarantees and compliance
- [Documentation](#documentation): all reference docs
- [Stability guarantees](#stability-guarantees): version axis, deprecations, toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
pip install crypto-service-sdk-python==0.0.41
python -c 'import crypto_service; print(crypto_service.USER_AGENT)'
```

The distribution is `crypto-service-sdk-python`; the import package is
`crypto_service`. With uv, `uv add crypto-service-sdk-python`. The only
run-time dependency is `httpx[http2]`. The package is typed (PEP 561,
`py.typed`) and checked with `mypy --strict`.

Each GitHub release carries the sdist and the wheel, a CycloneDX SBOM,
`SHA256SUMS` and a build provenance attestation; PyPI receives the same
sdist and wheel by trusted publishing, with PEP 740 attestations. The
first release is 0.0.40, in lockstep with the Crypto Service suite; until
it is on PyPI, install from a commit with
`pip install git+https://github.com/sebastienrousseau/crypto-service-sdk-python@<sha>`.

---

## Requirements

- Python 3.11 or newer ([toolchain policy](docs/POLICIES.md)). CI tests
  3.11, 3.12, 3.13 and 3.14 on Ubuntu 24.04; the package is pure Python
  and has no platform-specific code.
- `httpx` 0.28 or newer with its `http2` extra (installed with the
  package).
- A running crypto-server of the same version, started with an API key
  (`CRYPTO_API_KEY`) or a JWT secret (`JWT_SECRET`). The SDK does no
  cryptography itself: every operation is one HTTP call to the server.

---

## Quick Start

```python
import asyncio
import os

from crypto_service import ApiError, AsyncClient


async def main() -> None:
    async with AsyncClient(
        os.environ["CRYPTO_SERVICE_URL"], api_key=os.environ["CRYPTO_SERVICE_API_KEY"]
    ) as client:
        digest = await client.hash(algorithm="sha256", data="abc")
        print(digest["digest"])

        key = await client.generate_key_pair(algorithm="ed25519")
        signed = await client.sign(key_id=key["keyId"], message="hello")
        checked = await client.verify(
            public_key=key["publicKey"], message="hello", signature=signed["signature"]
        )
        print("valid:", checked["valid"])
        await client.keys_delete(key_id=key["keyId"])

        try:
            await client.sign(key_id=key["keyId"], message="hello")
        except ApiError as error:
            print(error.status, error.problem.type)


asyncio.run(main())
```

Set `CRYPTO_SERVICE_URL` (for example `http://127.0.0.1:3000`) and
`CRYPTO_SERVICE_API_KEY` to the server's `CRYPTO_API_KEY`. `hash`
returns the server's `data` member as a typed dict, here with the hex
`digest`. The Ed25519 private key never leaves the server:
`generate_key_pair` returns its `keyId` and public key, and `sign` takes
the `keyId`. Signing with the deleted key raises `ApiError` with status
404 and the problem type `urn:crypto-service:problem:key-not-found`.

The blocking client has the same methods without `await`:

```python
import os

from crypto_service import Client

with Client(
    os.environ["CRYPTO_SERVICE_URL"], api_key=os.environ["CRYPTO_SERVICE_API_KEY"]
) as client:
    print(client.hash(algorithm="blake3", data="abc")["digest"])
```

---

## The Crypto Service ecosystem

Crypto Service has one engine, crypto-server, and thin typed clients per
language. Every client vendors the same conformance kit from
crypto-service and runs it in CI against a live server built from the
commit in `ci/server.ref`, so they agree on behaviour.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`crypto-service`][core] | 18 npm packages, among them crypto-lib, crypto-server (the REST API this SDK calls), the TypeScript SDK, the CLI, MCP and LSP servers | The engine behind every SDK |
| **`crypto-service-sdk-python`** | Async and blocking Python client for the REST API | Python services, scripts and notebooks |
| [`crypto-service-sdk-java`][java], [`-rust`][rust], [`-go`][go], [`-cpp`][cpp], [`-dotnet`][dotnet] | The same client surface in Java, Rust, Go, C++ and .NET | Other languages, same behaviour |
| [crypto-service.co][site] | Product site, SDK pages and the published OpenAPI document | Evaluating the suite |
| Conformance kit (`conformance/`) | Request and response vectors every SDK sends and checks | Proving an SDK against the server it targets |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Service | `root`, `health`, `live`, `ready`, `algorithms` | Supported |
| Compliance | `get_dora_compliance` (DORA Articles 9 and 13), `get_cbom` (CycloneDX 1.6 CBOM) | Supported |
| Hashing and MACs | `hash` (SHA-2, SHA-3, BLAKE2b, BLAKE3), `mac`, `mac_verify` | Supported |
| Key derivation | `kdf` (scrypt, HKDF, PBKDF2), `password_hash`, `password_verify` (Argon2id) | Supported |
| Symmetric | `encrypt`, `decrypt`, `secretbox_seal`, `secretbox_open`, `password_encrypt`, `password_decrypt`, `key_wrap`, `key_unwrap` | Supported |
| Server-held keys | `generate_key_pair`, `export_key`, `keys_delete`, `sign`, `verify`, `stream_sign`, `stream_verify` | Supported |
| Post-quantum | ML-KEM-768, hybrid X25519 + ML-KEM-768, ML-DSA, SLH-DSA, ISO 20022 dual-signature checks | Supported |
| Public-key encryption | Sealed boxes, hybrid STREAM, multi-recipient, HPKE (RFC 9180) | Supported |
| KMS | `kms_create_key`, `kms_encrypt`, `kms_decrypt`, `kms_wrap`, `kms_unwrap`, `kms_generate_data_key` | Supported |
| OPAQUE | The server side of registration and login | Supported; the client side of OPAQUE is not in the SDK |
| Raw calls | `request()`: any method and path, status, headers and body back | Supported |
| v1 routes and `/metrics` | Deprecated v1 (sunset 2027-01-01) and the Prometheus endpoint | Through `request()` only |

All 59 v2 operations in the OpenAPI document have a typed method.

---

## Ecosystem comparison

Every Crypto Service SDK shares one method surface, one retry table and
one error model, and runs the conformance kit against a live
crypto-server in CI.

| Project | Language (minimum) | Conformance kit in CI | Async and blocking | Types |
| :--- | :---: | :---: | :---: | :---: |
| **crypto-service-sdk-python** | **Python 3.11** | **Yes** | **Both** | **TypedDict, mypy --strict** |
| `@sebastienrousseau/crypto-sdk` | TypeScript (Node 24) | In the server's tests | Async | TypeScript |
| crypto-service-sdk-java, -rust, -go, -cpp, -dotnet | Java, Rust, Go, C++, .NET | Yes | See each SDK | Hand-written |
| Raw HTTP with `httpx` | Python | No | Both | None |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the complete matrix.

---

## Benchmarks

The benchmarks use the four scenario names every Crypto Service SDK
shares: `encode_request`, `decode_response` and `decode_problem` measure
the client's own work with no network, and `round_trip_hash` is a
loopback round trip to a server (only when `CRYPTO_SERVICE_URL` is set).
They run with pytest-benchmark (`make bench`). No figures are published
yet: [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) describes the method,
and will hold results with the hardware they ran on.

---

## Features

- **Async first.** `AsyncClient` (asyncio) is the primary API; `Client`
  is generated from the same source by `scripts/unasync.py`, and CI
  fails if the two drift.
- **One method per v2 operation**, with keyword-only arguments in
  snake_case that map to the API's camelCase members.
- **Encodings as the API names them.** Arguments the API takes as hex or
  base64 accept `bytes` and encode them; `str` is sent unchanged.
  Responses keep the API's strings; `crypto_service.encoding.from_hex`
  and `from_base64` turn them into `bytes`. HPKE and KMS plaintexts follow
  the server's documented rules, never a guess.
- **Typed results.** Each method returns the response's `data` member as
  a `TypedDict` from `crypto_service.types` (or a `str` for the routes
  that answer a bare string), with no extra copies.
- **Errors.** `CryptoServiceError` is the base. `ApiError` carries the
  status and the RFC 9457 `Problem` (`type`, `title`, `status`, `detail`,
  `instance`, `code`, `errors` as `ValidationIssue`s, and the raw
  document); a body that is not a problem becomes an `about:blank`
  problem. `TransportError` covers no response, timeouts (`timed_out`),
  refused redirects and undecodable 2xx bodies
  ([ADR 0003](docs/adr/0003-error-model.md)).
- **One connection pool per client**: httpx with keep-alive and HTTP/2
  over TLS when the server offers it ([ADR 0002](docs/adr/0002-http-stack-httpx.md)).
- **Opt-in retries** with exponential backoff and full jitter,
  `Retry-After` honoured, and stateful operations never repeated after a
  504 or a lost connection.
- **Raw calls.** `request()` returns a `Response` for any route,
  whatever its status.

---

## Configuration

`AsyncClient` and `Client` take the server URL and these keyword
arguments:

| Option | Type | Default | Meaning |
| :--- | :--- | :--- | :--- |
| `api_key` | `str \| None` | None | Sent as `x-api-key`; CR, LF and NUL are refused |
| `token` | `str \| None` | None | A JWT, sent as `Authorization: Bearer` |
| `timeout` | `float \| None` | 30.0 | Seconds per attempt; None for none |
| `deadline` | `float \| None` | None | Seconds for the whole call, retries and waits included |
| `retry` | `RetryOptions \| None` | no retries | `max_retries` (0), `initial_delay` (0.2 s), `max_delay` (2.0 s) |
| `traceparent` | `str \| bool \| None` | None | A W3C `traceparent` to send, or True for a new one per call |
| `transport` | httpx transport | httpx's | An `httpx.AsyncBaseTransport` (`BaseTransport` for `Client`), for tests |

```python
import os

from crypto_service import Client, RetryOptions

client = Client(
    os.environ["CRYPTO_SERVICE_URL"],
    api_key=os.environ["CRYPTO_SERVICE_API_KEY"],
    timeout=10.0,
    deadline=30.0,
    retry=RetryOptions(max_retries=3, initial_delay=0.2, max_delay=2.0),
    traceparent=True,
)
print(repr(client))  # credentials show as '***'
print(client.ready()["status"])
client.close()
```

Retries apply to 429, 503 and 504 answers and to connection errors.
Operations that create or delete state (`keys_delete`,
`generate_key_pair`, every `*keygen*` method, `kms_create_key`,
`opaque_register_*`) are retried only after 429 or 503, which the server
sends before doing any work. A `Retry-After` longer than `max_delay` ends
the retries. The library reads no environment variables; the examples
and tests read `CRYPTO_SERVICE_URL` and `CRYPTO_SERVICE_API_KEY`.

---

## Examples

Each runs against a live crypto-server and is run by CI
(`make examples`, with `CRYPTO_SERVICE_URL` and `CRYPTO_SERVICE_API_KEY`
set).

| Example | Shows | Run |
| :--- | :--- | :--- |
| [`hash.py`](examples/hash.py) | The blocking `Client`: SHA-256, SHA3-256 and BLAKE3 digests | `python examples/hash.py [text]` |
| [`aead_round_trip.py`](examples/aead_round_trip.py) | `encrypt` and `decrypt` under a caller-held 256-bit key | `python examples/aead_round_trip.py` |
| [`ed25519_sign_verify.py`](examples/ed25519_sign_verify.py) | A server-held Ed25519 key: sign by `keyId`, verify, delete | `python examples/ed25519_sign_verify.py` |
| [`ml_kem.py`](examples/ml_kem.py) | ML-KEM-768 encapsulation and decapsulation by `keyId` | `python examples/ml_kem.py` |
| [`problem_details.py`](examples/problem_details.py) | `ApiError` and its problem, validation issues, `request()`, `TransportError` | `python examples/problem_details.py` |
| [`concurrent_requests.py`](examples/concurrent_requests.py) | Concurrent calls with `asyncio.gather` over one pool, with retries on 429 | `python examples/concurrent_requests.py` |

---

## When not to use Crypto Service

- **You cannot run a crypto-server.** The SDK is a client; every
  operation is a call to the server, and nothing works offline.
- **You need cryptography in-process.** Use a local library (for example
  `cryptography` or `pynacl`); this SDK sends plaintexts and keys you
  pass it to the server, so use `https://` for anything off loopback.
- **You need the v1 routes or `/metrics` typed.** v1 is deprecated (sunset
  2027-01-01) and `/metrics` is for Prometheus; both are reachable only
  through `request()`.
- **You need the client side of OPAQUE.** The SDK carries the messages
  an OPAQUE client library produces; it does not produce them.
- **You need one client across event loops.** An `AsyncClient` belongs
  to the event loop that first uses it; create one per loop, or use
  `Client` from threads.
- **You need large payloads streamed.** Requests and responses are JSON
  held in memory; the server bounds body sizes.

---

## Development

Clone the repository, then, with [uv](https://docs.astral.sh/uv/) and
[mise](https://mise.jdx.dev/) (`mise install` pins the toolchain):

```sh
make check
```

`make check` runs the version checks, the generated-client check, ruff
(lint and format), `mypy --strict`, the complexity ceilings (cyclomatic
10, cognitive 15, Halstead difficulty 30, 60 lines per function, 500 per
file) and the unit tests at 100% line and branch coverage.
`make conformance` runs the kit against the server at
`CRYPTO_SERVICE_URL` and fails, not skips, without one;
`make regression` starts a crypto-server from a built checkout and runs
everything against it. `make fuzz` runs the atheris targets, `make bench`
the benchmarks, `make audit` pip-audit, and `make demo` re-renders the
GIF above with [VHS](https://github.com/charmbracelet/vhs).
[`DEVELOPMENT.md`](DEVELOPMENT.md) maps every CI gate to its command.

---

## Security

The SDK sends the data and keys you pass it to the server you configure
and nothing else. It never logs. Exception messages and `repr` hold the
status, the problem type and its title, never a request or response
body, the problem's `detail` or a credential; a client's `repr` shows
credentials as `'***'`. Redirects are refused, so credentials cannot
reach another origin, and TLS verification is always on, with no option
to turn it off. Credentials are checked for CR, LF and NUL so they cannot
inject headers. The problem parser and the response decoder are fuzzed
with atheris on every pull request, and their seed corpus replays in the
unit tests. Releases carry SHA256SUMS, a CycloneDX SBOM and a build
provenance attestation.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[Manual](docs/index.md) · [Developer docs](DEVELOPMENT.md) ·
[Family map](#the-crypto-service-ecosystem)

Also: [Architecture](docs/ARCHITECTURE.md) ·
[Decision records](docs/adr/README.md) · [Roadmap](docs/ROADMAP.md) ·
[Benchmarks](docs/BENCHMARKS.md) · [Comparison](docs/COMPARISON.md) ·
[Policies](docs/POLICIES.md) · [Changelog](CHANGELOG.md) ·
[Contributing](CONTRIBUTING.md) · [Governance](GOVERNANCE.md) ·
[Support](SUPPORT.md) · [Conformance kit](conformance/README.md) ·
[Agent rules](AGENTS.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in
lockstep with the Crypto Service suite: SDK 0.0.N vendors the
conformance kit from crypto-service 0.0.N and is tested against that
server. The breaking axis is the public API of `crypto_service`: a
removed or renamed method, argument, type or exception, or a different
exception for a given response, is breaking and the changelog calls it
out; CI compares the public API with the last release tag (griffe).
Modules whose names start with an underscore are private. The SDK passes
the server's answers through unchanged: a different answer to the same
request is a server change, recorded in crypto-service. The v1 API and
`/metrics` are not part of the SDK. The Python floor moves only as
described in the [toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

- Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
- MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Dependencies keep their own licences: httpx (BSD-3-Clause)
and, through it, h2, httpcore, anyio, certifi and idna.

[core]: https://github.com/sebastienrousseau/crypto-service
[java]: https://github.com/sebastienrousseau/crypto-service-sdk-java
[rust]: https://github.com/sebastienrousseau/crypto-service-sdk-rust
[go]: https://github.com/sebastienrousseau/crypto-service-sdk-go
[cpp]: https://github.com/sebastienrousseau/crypto-service-sdk-cpp
[dotnet]: https://github.com/sebastienrousseau/crypto-service-sdk-dotnet
[site]: https://crypto-service.co
