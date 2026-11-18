<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Assurance case

This is the argument that `crypto-service-sdk-python` meets its security
requirements, and the evidence for each step. The claim: **the SDK sends
what its caller asks for to the configured crypto-server and nowhere
else, over a verified connection when the URL is `https://`, does not
leak credentials or data through its own outputs, and hands back only
values that have the shape the API documents.** It does not claim to
protect data from the server it is pointed at: the server does all the
cryptography ([ADR 0001](adr/0001-thin-client-over-the-server.md)).

Code references are to `src/crypto_service/`; test references are to
`tests/`. [SECURITY.md](https://github.com/sebastienrousseau/crypto-service-sdk-python/blob/main/SECURITY.md)
summarises the same measures for users;
[the 2026-11 security review](security-review-2026-11.md) checked this
document against the code.

## Threat model

### Assets

| Asset | Where it lives in the SDK |
| :--- | :--- |
| Credentials: API key, bearer token (JWT) | `Config.api_key`, `Config.token` (`_core.py`), sent as headers |
| Caller data: plaintexts, messages, passwords, symmetric keys, key IDs | Request bodies, built per call, never stored |
| Server answers: ciphertexts, signatures, shared secrets, exported keys, verification results | Response bodies, returned to the caller |
| The integrity of a verification result (`valid`, `allValid`) | Decoded from the response; the caller acts on it |
| The released package and its provenance | sdist and wheel on GitHub and PyPI, built by `release.yml` |

### Actors

| Actor | Trust | What they can do |
| :--- | :--- | :--- |
| The calling application and its operator | Trusted | Chooses `base_url`, credentials, inputs, the process environment and an optional `transport` |
| The crypto-server at `base_url` | Trusted for the data sent to it | Sees every plaintext and key the caller sends; answers every call |
| A network attacker between the two | Untrusted | Reads and changes `http://` traffic; with `https://`, can only drop, delay or misroute it |
| A malicious or compromised server or proxy | Untrusted for the caller's process | Sends redirects, slow, huge, malformed or mistyped responses, misleading problem documents |
| Input from the caller's own users that reaches SDK arguments | Untrusted | Strings in paths, headers or bodies, when the caller passes them through |
| Upstream maintainers of dependencies, GitHub Actions and registries | Partly trusted | Could ship a compromised httpx, h2, action or toolchain |
| Package users downloading a release | Need to verify | Check signatures, checksums and attestations ([REPRODUCING.md](REPRODUCING.md)) |

### Entry points

1. **Client construction**: `AsyncClient(...)` and `Client(...)`, whose
   options pass through `Config.create` in `_core.py`.
2. **Typed methods** (`_async/_meta.py` to `_async/_opaque.py`, and the
   generated `_sync/` twins): arguments become a JSON body for a fixed
   method and path.
3. **The raw call** `request(method, path, body=, content=, headers=)`
   in `_async/_base.py`: the one place a caller chooses the method, the
   path and extra headers.
4. **Responses**: status, headers and body from the server, decoded by
   `_core.decode_response`, `_problem.parse_problem` and
   `_shape.check_shape`.
5. **The process environment**, read by httpx (not by the SDK): proxy
   variables and `SSL_CERT_FILE` / `SSL_CERT_DIR`.
6. **The supply chain**: `uv.lock`, the pinned actions in
   `.github/workflows/`, the build backend, and the release workflow.

## Trust boundaries

```text
 caller code ──(1)── SDK ──(2)── httpx / network ──(3)── crypto-server
                      │
                      └──(4)── process environment (proxies, CA roots)

 source ──(5)── CI and release workflows ──(6)── GitHub release, PyPI ──(7)── user
```

| Boundary | What crosses it | What the SDK does there |
| :--- | :--- | :--- |
| (1) Caller to SDK | Options and arguments | Validates every option that reaches a URL or a header against an allowlist (`Config.create`, `check_request_target`, `_check_extra_headers`); JSON-encodes bodies (`encode_body`), so arguments cannot change the request's structure; the server validates body members, as the authority on them. |
| (2) SDK to network | One HTTP request | Sends credentials only to `base_url` (no redirects, no absolute paths in `request()`); TLS verification on, with no option to disable it; `http://` allowed, documented for loopback use. |
| (3) Server to SDK | Status, headers, body | Treats the answer as untrusted input: 3xx refused, 4xx and 5xx parsed into a `Problem` without raising on any bytes, 2xx checked to be JSON, wrapped where the route wraps, and of the declared type before it is returned. |
| (4) Environment to httpx | Proxy settings, CA roots | Not mediated by the SDK. Documented in SECURITY.md: whoever controls the process environment chooses the proxy and the trusted roots. |
| (5) Source to CI | Pull requests | Workflows run with `contents: read` unless a job needs more, actions pinned by commit SHA, `persist-credentials: false`, the crypto-server checkout fetched by a validated 40-character SHA; no `pull_request_target`. |
| (6) CI to registries | Release files | Only from a signed annotated tag verified against `KEYS.asc`; PyPI by trusted publishing (OIDC, no stored token) from the `release` environment; Sigstore build provenance on every file; PEP 740 attestations on PyPI. |
| (7) Registries to user | Downloads | `SHA256SUMS`, `gh attestation verify`, and a reproducible build ([REPRODUCING.md](REPRODUCING.md)). |

## Secure design principles

Saltzer and Schroeder's principles, as this code applies them.

| Principle | How it is applied | Evidence |
| :--- | :--- | :--- |
| **Economy of mechanism** | No cryptography in the client; one dependency (`httpx[http2]`). Every rule that does not touch the network lives once, sans I/O, in `_core.py`, `_shape.py` and `_problem.py`; the blocking client is generated from the async one (`scripts/unasync.py`), so the two cannot drift. Complexity ceilings are enforced in CI (`scripts/check_complexity.py`). | `make unasync-check`, `make complexity` |
| **Fail-safe defaults** | Retries off by default; redirects never followed; TLS verification always on; a 30-second per-attempt timeout; a response that is not of the declared type is an error, not a partially filled result; a stateful call is never repeated after an ambiguous failure. Validation is by allowlist, so an unforeseen character is refused rather than passed on. | `test_no_retry_by_default`, `test_redirects_are_refused`, `test_operation_refuses_a_mistyped_answer`, `test_stateful_routes_are_not_retried_after_504` |
| **Complete mediation** | Every typed method goes through `AsyncBase._call`, and `request()` through the same `_send`; there is no other path to the network. Every header value the caller can influence is checked when the configuration is built (`Config.create`) or when the raw call is made (`check_request_target`, `Config.headers`). Every 2xx body passes `decode_response` and `check_shape`. | `test_every_typed_method_is_exercised`, `test_raw_request_target_is_checked`, `test_extra_headers_are_checked` |
| **Least privilege** | Public probes and OPAQUE login are sent without credentials (`auth=False`). Workflows default to `contents: read` and grant `id-token`, `attestations` or `contents: write` only to the release jobs that need them. Key export needs a scope `crypto:admin` does not imply (server side, documented on `export_key`). | `check_credentials` in `test_operations.py`; `permissions:` blocks in `.github/workflows/` |
| **Open design** | The source, the threat model, this argument and the conformance kit are public; security does not rest on obscurity of the client. | This repository |
| **Separation of privilege** | Publishing to PyPI needs a `v*` tag whose signature verifies against `KEYS.asc` **and** the maintainer's approval of the `release` environment (a required reviewer; only `v*` tags may deploy to it). No PyPI token exists to steal: PyPI trusts this workflow and environment only. | `release.yml` (`git verify-tag`, `environment: release`); environment protection rules |
| **Least common mechanism** | Each client instance owns its connection pool and its immutable `Config`; the only module-level state is a cache of the response types' annotations, which never changes once built. Each call keeps its own attempt count, deadline and traceparent. | `Config` is `frozen=True`; `docs/ARCHITECTURE.md`, Concurrency |
| **Psychological acceptability** | Secure behaviour needs no configuration: verification, redaction and validation are on by default and cannot be turned off; credentials show as `'***'` in `repr`, so logging a client is safe. | `test_repr_redacts_credentials`, `test_config_defaults_and_repr` |

## Common weaknesses

The CWE Top 25 (2024) and OWASP Top 10 (2021) entries that apply to an
HTTP client library, and the ones that do not.

| Weakness | Counter-measure | Code | Test or check |
| :--- | :--- | :--- | :--- |
| CWE-20 Improper input validation; OWASP A03 Injection | Allowlists for every value that reaches a request line or header; bodies JSON-encoded, never concatenated | `_core.py`: `_FIELD_VALUE`, `_TOKEN68`, `_TOKEN`, `_TRACEPARENT`, `check_request_target`, `encode_body` | `test_api_key_is_visible_ascii`, `test_token_is_token68`, `test_traceparent_follows_w3c_trace_context`, `test_raw_request_target_is_checked`, `test_extra_headers_are_checked` |
| CWE-113 HTTP response splitting / header injection (CWE-93) | CR, LF, NUL and every other control character are outside the allowlists | as above | as above |
| CWE-200, CWE-532 Exposure of sensitive information (logs, errors); OWASP A09 | The SDK never logs; exception messages carry status, problem type and title only; `detail`, bodies and credentials are `repr=False`; validation errors never repeat the value | `errors.py`, `_core.Config.describe`, `_shape._fail` | `test_api_error_carries_the_problem`, `test_repr_redacts_credentials`, `test_check_shape_names_the_member_not_the_value` |
| CWE-522 Insufficiently protected credentials; CWE-601 open redirect | No redirects; `request()` refuses absolute and network-path references; `base_url` may not carry user information | `_async/_base.py` (`follow_redirects=False`), `check_request_target`, `_check_base_url` | `test_redirects_are_refused`, `test_raw_request_stays_on_the_base_url`, `test_base_url_is_checked` |
| CWE-295 Improper certificate validation; CWE-319 cleartext transmission; OWASP A02 | httpx verification on, no option to disable; `http://` documented as loopback-only | `_async/_base.py` (no `verify` argument) | Review: `AsyncBase.__init__` exposes no TLS option; httpx's default context (TLS 1.2 minimum, hostname check) |
| CWE-502 / CWE-20 on responses; OWASP A08 Software and data integrity | JSON only (no pickle, no eval); 2xx bodies checked against the declared `TypedDict`, `Literal` values enforced, `bool` not accepted as `int`; error bodies parsed defensively | `_core.decode_success`, `_shape.py`, `_problem.py` | `test_operation_refuses_a_mistyped_answer`, `test_check_shape_*`, `test_never_raises_on_bytes`; atheris targets `fuzz/fuzz_problem.py`, `fuzz/fuzz_response.py` |
| CWE-674 Uncontrolled recursion | `RecursionError` from deeply nested JSON is caught and reported as an undecodable body; `check_shape` recurses only as deep as the declared type | `_core.decode_success`, `_problem._object` | fuzz targets |
| CWE-400 / CWE-770 Uncontrolled resource consumption | Per-attempt timeout and an optional overall deadline (wall-clock in `AsyncClient`); bounded, jittered retries; a `Retry-After` beyond `max_delay` ends the retries. **Accepted:** bodies are read without a size limit, and the blocking client's timeout is per socket operation | `_core.Deadline`, `backoff_delay`, `delay_after_status` | `test_deadline_bounds_retries_of_slow_attempts`, `test_long_retry_after_ends_the_retries` |
| CWE-330 Insufficiently random values | Retry jitter and traceparent IDs come from `secrets` | `_core._JITTER`, `generate_traceparent` | `test_generated_traceparent_is_valid` |
| Repeated side effects (not a CWE Top 25 entry) | Stateful routes retried only after 429 or 503, never after a lost connection or a 504 | `_core._STATEFUL_ROUTE`, `is_idempotent` | `test_retry_safety_table`, `test_connection_errors_are_not_retried_when_stateful` |
| OWASP A06 Vulnerable and outdated components; CWE-1395 | One run-time dependency; `uv.lock` with hashes; pip-audit on every push; Dependabot weekly; CodeQL (Python and Actions); OpenSSF Scorecard | `uv.lock`, `Makefile` `audit`, `.github/dependabot.yml`, `.github/workflows/codeql.yml` | CI `lint` job |
| Supply chain (OWASP A08) | Actions pinned by SHA; trusted publishing; signed tags; Sigstore provenance; reproducible sdist, wheel and SBOM | `.github/workflows/release.yml`, `scripts/sbom.sh` | [REPRODUCING.md](REPRODUCING.md); CI compares two SBOM runs |

Not applicable: memory-safety weaknesses (CWE-787, CWE-125, CWE-416,
CWE-476: pure Python, no native code of its own), SQL and OS command
injection (CWE-89, CWE-78: no database, no subprocess in the library),
XSS and CSRF (CWE-79, CWE-352: no HTML, no browser), path traversal
(CWE-22: no file access), missing authentication or authorization
(CWE-306, CWE-862, CWE-863: enforced by the server, which the SDK only
calls), hard-coded credentials (CWE-798: none; tests and examples use
synthetic values or environment variables), and cryptographic weaknesses
in the client (OWASP A02 beyond transport: the client implements none).

## Assertions

The library has no `assert` statements, on purpose. Python removes
`assert` under `python -O`, so an invariant that matters cannot rest on
one: the checks that guard behaviour are explicit and always on, and
raise the SDK's own exceptions (`ValueError` for bad options,
`TransportError` for a response that is not what the API promises,
`ApiError` for an error status). Run-time invariants are therefore
checked in production builds, not only in debug runs. The fuzz targets
(`fuzz/targets.py`) state their invariants with a helper that raises
`AssertionError` without `assert`, so they hold under `-O` too; the
tests use pytest's `assert`.

## Residual risks

These are accepted, and documented for users:

- A server, or a proxy the caller configured, sees every plaintext and
  key sent to it. That is the design (ADR 0001); use `https://` and a
  server you control.
- `http://` is accepted for any host, so a misconfigured production URL
  sends credentials in clear. It is documented; refusing it would break
  TLS-terminating sidecars on loopback or a private network.
- The process environment can change the CA roots and route traffic
  through a proxy (httpx `trust_env`).
- A malicious server can make the blocking client wait longer than its
  timeout and deadline by trickling bytes, and can send a body large
  enough to exhaust memory.
- The release build job runs the test gate with `id-token: write`, so a
  compromised locked development dependency could request a provenance
  attestation; see the security review.
