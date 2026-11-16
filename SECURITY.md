<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

This package follows the [Crypto Service](https://github.com/sebastienrousseau/crypto-service)
suite cadence. While pre-`1.0`, the latest released `0.0.x` receives
security fixes; older `0.0.x` versions do not. `0.0.40` is the first
release of this SDK.

| Version | Status | Receives security fixes? |
| :--- | :--- | :--- |
| `0.0.40` (latest) | Current | Yes |
| `main` | In development | Yes |

## Reporting a vulnerability

**Do not open a public issue for security reports.**

Use GitHub Private Vulnerability Reporting:
<https://github.com/sebastienrousseau/crypto-service-sdk-python/security/advisories/new>.
The maintainer is notified automatically. A vulnerability in crypto-server
or crypto-lib belongs in
[crypto-service's advisories](https://github.com/sebastienrousseau/crypto-service/security/advisories/new).

Please include a description and its impact, a minimal reproducer
(preferably a failing test), the commit or version affected, and any
proposed fix. Use synthetic keys and credentials only.

These are goals, not guarantees: the project is maintained in a personal
capacity, with no SLA. **Acknowledgement**: the goal is within 5 working
days. **Triage**: a severity assessment and remediation plan after
acknowledgement.

## Security posture

### Scope

The SDK is an HTTP client. It builds JSON requests, sends them with
httpx to the server named by `base_url`, and decodes the JSON responses.
It implements no cryptography ([ADR 0001](docs/adr/0001-thin-client-over-the-server.md)):
keys, plaintexts and messages you pass to it are sent to the server.

### Threat model

| Surface | How it is handled |
| :--- | :--- |
| **Secrets in logs and errors** | The SDK never logs. Exception messages and `repr` carry the status, problem type and title only; `detail`, bodies and credentials are never included. A client's `repr` shows credentials as `'***'`. |
| **Header injection** | An API key, token or traceparent containing CR, LF or NUL is refused with `ValueError`, whose message does not repeat the value. |
| **Redirects** | Never followed (`follow_redirects=False`); a 3xx raises `TransportError`, so credentials cannot reach another origin. |
| **TLS** | Verification is httpx's default (on, with certifi's roots); the SDK has no option to turn it off. An injected `transport` is the caller's responsibility. |
| **Credentials in the URL** | A `base_url` with user information, a query or a fragment is refused. |
| **Plain-text transport** | `http://` is accepted for loopback development; use `https://` elsewhere, as keys and plaintexts travel in the request. |
| **Malformed responses** | A 2xx body that is not JSON, or lacks `data` where the route wraps it, raises `TransportError`; any error body becomes a `Problem`. Both parsers are fuzzed. |
| **Repeated side effects** | Stateful operations are never retried after a lost connection or a 504. |

### Dependency audit

`make audit` runs pip-audit over every locked dependency in `uv.lock`,
development tools included; CI runs it on every push. Dependabot proposes
weekly updates of `uv.lock` and of the pinned workflow actions.
