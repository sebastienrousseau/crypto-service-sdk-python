<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
advance in `0.0.1` steps in lockstep with the Crypto Service suite.

## [0.0.40] - Unreleased

The first release, in lockstep with crypto-service 0.0.40.

### Added

- `AsyncClient` (asyncio, the primary API) and `Client` (blocking,
  generated from the async source) for the crypto-server v2 API: one
  typed method per v2 operation (59), plus `root`, `health`, `live`,
  `ready`, `algorithms`, `get_dora_compliance`, `get_cbom` and a raw
  `request()`.
- Options from the suite's SDK contract: `api_key`, `token`, `timeout`
  (30 s per attempt), `deadline`, `retry` (`RetryOptions`, off by
  default), `traceparent` and `transport`.
- Retries with exponential backoff and full jitter, `Retry-After`
  honoured up to `max_delay`, and the retry-safety table of the
  TypeScript SDK: stateful operations retry only after 429 or 503.
- `ApiError` with the RFC 9457 `Problem` (`ValidationIssue`s for
  `errors[]`), `TransportError` with `timed_out`, both under
  `CryptoServiceError`.
- Typed responses (`crypto_service.types`) and the encoding helpers in
  `crypto_service.encoding`.
- The conformance kit vendored from crypto-service at `ci/server.ref`,
  with a runner that sends every vector through the SDK.
- Examples, pytest-benchmark scenarios, atheris fuzz targets, CI, the
  release workflow with PyPI trusted publishing, and the documentation.
