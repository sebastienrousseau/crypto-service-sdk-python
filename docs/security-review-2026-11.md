<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Security review, November 2026

| | |
| :--- | :--- |
| **Date** | 2026-11-18 |
| **Reviewer** | Sebastien Rousseau, with AI-assisted analysis (Claude) |
| **Baseline** | `main` at `14f000f` (release 0.0.40), and the 0.0.41 changes on `feat/v0.0.41` |
| **Against** | [The assurance case](ASSURANCE.md) |

## Scope

- The library, `src/crypto_service/`: configuration and header
  building, the request loop, retries, timeouts and the deadline, the
  raw `request()` call, response and problem decoding, exceptions and
  their messages, the generated blocking client.
- Transport and TLS: how httpx is configured, what it reads from the
  environment.
- Credential handling: where the API key and token go, and where they
  must never appear.
- CI and release: the seven workflows, their permissions, pinned
  actions, the server checkout, the release and publish jobs, the
  release environment's protection rules.
- Dependencies: `uv.lock`, the Dependabot configuration and its recent
  runs.

Out of scope: crypto-server and crypto-lib (reviewed in crypto-service),
the conformance kit (vendored, checksummed), and the project homepage.

## Method

1. Read every module of the library and the workflows, against each
   trust boundary and weakness of the assurance case.
2. Reproduced each suspected issue with a script against the 0.0.40
   code (a mock transport, a local HTTP server, or a socket server that
   sends one byte every 100 ms) before calling it a finding.
3. For each finding that is a bug: a test that fails on the old code,
   the fix, and the full gate (`make check`: lint, `mypy --strict`,
   complexity ceilings, 100% line and branch coverage on Python 3.11 to
   3.14), then `make regression` against crypto-server at
   `ci/server.ref` (conformance kit 119/119 through the typed methods,
   examples, README blocks).
4. Ran the response fuzz target for 60 seconds after extending it to the
   new type checks (8.7 million runs, no crash).
5. Read the Dependabot logs of 2026-11-16, the release environment's
   protection rules and the repository rulesets through the GitHub API.

## Findings

| # | Severity | Finding | Disposition |
| :--- | :--- | :--- | :--- |
| 1 | Medium | `request()` sent an absolute URL as given | Fixed |
| 2 | Low | Success responses were not checked against their types | Fixed |
| 3 | Low | Input validation was a denylist | Fixed |
| 4 | Low | The blocking client's timeout and deadline are not wall-clock limits | Documented, accepted |
| 5 | Low | httpx reads proxy and CA-root variables; the docs said the library reads none | Documented, accepted |
| 6 | Low | The release build job holds `id-token: write` while it runs the test gate | Accepted, follow-up |
| 7 | Low | The release SBOM was not reproducible | Fixed |
| 8 | Low | Dependabot's uv updates failed | Fixed |
| 9 | Info | Response bodies are read without a size limit | Accepted |
| 10 | Info | `http://` is accepted for any host | Accepted |
| 11 | Info | `KEYS.asc` is read from the tagged commit | Accepted |

### 1. `request()` sent an absolute URL as given (Medium, fixed)

`client.request("GET", "https://other.test/x")` sent the request, with
`x-api-key` or `Authorization`, to `other.test`: httpx uses an absolute
URL instead of joining it to `base_url`. A caller who builds the path
from its own users' input could leak the credentials to a host of the
attacker's choosing (CWE-522), bypassing the refusal of redirects. A
network-path reference (`//other.test/x`) silently lost its host.

Fix: `_core.check_request_target` refuses a path with a scheme or a
host, spaces or control characters, and a method that is not an RFC 9110
token, with `ValueError` before anything is sent. Tests:
`test_raw_request_stays_on_the_base_url` (no request reaches the
transport) and `test_raw_request_target_is_checked`, both failing on
0.0.40.

### 2. Success responses were not checked against their types (Low, fixed)

A 2xx body was checked to be JSON and, where the route wraps it, to have
a `data` member; its contents were cast to the `TypedDict` unchecked. A
server, or anyone on an `http://` path, could return
`{"valid": "false"}`, which is truthy in Python, or omit a member the
caller then indexes. The verification result is an asset in the threat
model.

Fix: every typed method passes its result type to the decoder, and
`_shape.check_shape` checks required members, JSON types (`bool` is not
an `int`), `Literal` values, list items and mapping values. A mismatch
raises `TransportError` naming the member path, never the value.
Members the type does not declare are kept, so a newer server can add
some. `__required_keys__` turned out to count `NotRequired` members as
required when annotations are strings (Python 3.11 to 3.14), so the
checker reads the annotations itself. Tests:
`test_operation_refuses_a_mistyped_answer` (every typed method, both
clients) and `test_check_shape_*`.

### 3. Input validation was a denylist (Low, fixed)

Credentials and the traceparent were refused only for CR, LF or NUL. A
non-ASCII API key passed construction and raised `UnicodeEncodeError`
(not a `CryptoServiceError`) on the first authenticated call; a raw
request header containing CR LF was refused by h11 only at send time,
reported as "the connection failed". Neither was injectable, because
httpx's HTTP/1.1 and HTTP/2 layers refuse such values, but the SDK's
behaviour depended on that.

Fix: allowlists in `_core.py`: the API key is visible ASCII with inner
spaces (RFC 9110 field-content), the token is token68 (RFC 7235), the
traceparent the W3C Trace Context format with non-zero IDs, raw header
names are tokens and values visible ASCII. Tests:
`test_api_key_is_visible_ascii`, `test_token_is_token68`,
`test_traceparent_follows_w3c_trace_context`,
`test_extra_headers_are_checked`, with the accepting counterparts.

### 4. The blocking client's timeout and deadline are not wall-clock limits (Low, documented)

`Client(url, timeout=0.5, deadline=1.0).live()` against a server that
sends one byte every 100 ms returned after 4.1 seconds; `AsyncClient`
raised `TransportError` after 0.5 seconds. In the blocking client httpx
applies `timeout` to each socket operation, and the deadline is checked
only between attempts. The README described both as limits for the
attempt and the call.

Disposition: the README configuration section and SECURITY.md now say
so, and point to `AsyncClient` when a hard bound matters. Enforcing a
wall-clock limit in blocking code needs a watchdog thread that closes
the connection, which is more mechanism than the risk (a malicious or
broken server delaying its own caller) justifies.

### 5. httpx reads proxy and CA-root variables (Low, documented)

The README said the library reads no environment variables and
SECURITY.md that TLS uses certifi's roots. httpx, with its default
`trust_env=True`, honours `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`,
`NO_PROXY`, and `SSL_CERT_FILE` or `SSL_CERT_DIR`, which replace the
roots (`httpx/_config.py`).

Disposition: the README and SECURITY.md state it. The behaviour stays:
the process environment belongs to the operator, and corporate proxies
and private CAs depend on it.

### 6. The release build job holds `id-token: write` while it runs the test gate (Low, accepted)

The `build` job of `release.yml` runs `make check` (the development
tools and the test suite) and `make build` with `id-token: write` and
`attestations: write`, which it needs for the provenance step. A
compromised development dependency could use the job's OIDC token to
attest a file of its choosing as built by this workflow.

Disposition: accepted for 0.0.41, because every development dependency
is locked with hashes and audited, and the release path cannot be
exercised before a release. Follow-up: move the attestation into its own
job that downloads the built files and runs nothing else.

### 7. The release SBOM was not reproducible (Low, fixed)

The wheel and sdist of 0.0.40 rebuild bit for bit, but only with the
hatchling of the day (`hatchling>=1.27`; 1.29.0 gives other bytes), and
the SBOM was written from a `python3 -m venv` environment: it recorded
the runner's path to the wheel and the pip that Ubuntu seeded.

Fix: `tool.uv.build-constraint-dependencies` pins hatchling 1.33.0;
`scripts/sbom.sh` builds the SBOM from `uv.lock` with hashes, without
pip and without local paths; CI runs it twice per pull request and
compares the bytes. [REPRODUCING.md](REPRODUCING.md) gives the procedure
and the expected digests.

### 8. Dependabot's uv updates failed (Low, fixed)

The weekly uv run of 2026-11-16 ended with
`dependency_file_not_resolvable`: pymdown-extensions 13.1 needs Python
3.11.5, the lock covered 3.11.0 and up, and Dependabot's
`uv lock --upgrade-package pymdown-extensions==13.1` cannot hold two
versions. Every later uv update would have failed the same way, leaving
the locked tools without automated updates.

Fix: `tool.uv.environments` limits the lock to Python 3.11.5 and newer;
Dependabot's command resolves (reproduced with uv 0.13.1). The package
still declares `requires-python >= 3.11`.

### 9. Response bodies are read without a size limit (Info, accepted)

httpx reads each body whole. A malicious server can exhaust the
caller's memory (CWE-400). The server is trusted with the caller's data
already; a limit would need streaming every response. Documented in
SECURITY.md.

### 10. `http://` is accepted for any host (Info, accepted)

Credentials and data travel in clear over `http://`. It is documented
as for loopback development; refusing it for other hosts would break
TLS-terminating sidecars.

### 11. `KEYS.asc` is read from the tagged commit (Info, accepted)

`release.yml` verifies the tag against the `KEYS.asc` of the commit the
tag points to, so someone with write access could add a key on a branch
and tag it. Publishing to PyPI still needs the maintainer's approval of
the `release` environment (required reviewer, `v*` tags only); the
GitHub release job has no such gate. Today the maintainer is the only
person with write access.

## Checked, no finding

- Exceptions and `repr`: no credential, body, `detail` or argument
  value in messages; `Problem.raw`, `Response.headers` and
  `Response.content` are `repr=False`.
- Redirects off; TLS verification not configurable; `base_url` without
  user information, query or fragment.
- The retry-safety table matches the stateful routes; a 504 or a lost
  connection never repeats a key generation, deletion or OPAQUE
  registration.
- Randomness from `secrets`; JSON encoded with `allow_nan=False`;
  `RecursionError` and over-long integers in JSON handled.
- Workflows: `permissions` minimal per job, every action pinned by
  commit SHA, `persist-credentials: false` on every checkout, no
  `pull_request_target`, the crypto-server ref validated as a 40-hex SHA
  before it is fetched. CodeQL scans Python and Actions.
- Open alerts on 2026-11-18: none from Dependabot or secret scanning;
  one Scorecard alert (CII Best Practices badge in progress), which this
  work addresses.
