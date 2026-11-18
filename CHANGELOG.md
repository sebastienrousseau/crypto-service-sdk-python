<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions
advance in `0.0.1` steps in lockstep with the Crypto Service suite.

## [0.0.41] - Unreleased

### Added

- `docs/ASSURANCE.md`, the assurance case: threat model, trust
  boundaries, secure design principles and CWE/OWASP mapping, each with
  the code and tests behind it.
- `docs/security-review-2026-11.md`, the first recorded security review,
  with its findings and their disposition.
- `docs/REPRODUCING.md`: verify a release (tag signature, `SHA256SUMS`,
  `gh attestation verify`, PyPI provenance) and rebuild it bit for bit.
- `scripts/sbom.sh`, a reproducible release SBOM (from `uv.lock`, no
  pip, no local paths); CI checks two runs give the same bytes.
- The README demo, `.github/demo.gif`, rendered with `make demo`.

### Changed

- Typed methods check each success response against its type in
  `crypto_service.types` (required members, JSON types, `Literal`
  values, list items and mapping values) and raise `TransportError`
  naming the member, never its value, when it does not match. Members a
  newer server adds are kept.
- Input checks are allowlists: `api_key` must be visible ASCII (inner
  spaces allowed), `token` a token68 string such as a JWT, a string
  `traceparent` a W3C Trace Context value; `request()` checks its
  method (an RFC 9110 token), its path and its extra headers. Each
  raises `ValueError` without repeating the value.

### Fixed

- `request()` refuses a path with a scheme or a host
  (`https://other.test/x`, `//other.test/x`): an absolute URL was sent
  as given, with the client's credentials, to that other origin.
- Dependabot's uv updates: the lock now covers Python 3.11.5 and newer
  (`tool.uv.environments`), so `uv lock --upgrade-package` resolves; it
  failed on 2026-11-16 over pymdown-extensions 13.1. The build backend
  is pinned (`tool.uv.build-constraint-dependencies`) so releases
  rebuild bit for bit.
- Documentation: the blocking client's `timeout` and `deadline` bound
  each socket operation, not the whole attempt; httpx honours the proxy
  and `SSL_CERT_FILE`/`SSL_CERT_DIR` variables; the README no longer says
  the package is not yet on PyPI.

## [0.0.40] - 2026-11-16

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
