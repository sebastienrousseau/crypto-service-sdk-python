<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Security Policy

## Supported versions

This package follows the [Crypto Service](https://github.com/sebastienrousseau/crypto-service)
suite cadence. While pre-`1.0`, the latest released `0.0.x` receives
security fixes; older `0.0.x` versions do not. `0.0.40` is the first
release of this SDK.

| Version | Status | Receives security fixes? |
| :--- | :--- | :--- |
| `0.0.41` (latest) | Current | Yes |
| `0.0.40` | Previous | Until 0.0.41 is released |
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
| **Header injection** | Allowlists, not denylists: an API key must be visible ASCII, a token a token68 string, a traceparent a W3C value; a raw `request()` method must be an HTTP token, its header names tokens and values visible ASCII. Anything else raises `ValueError`, whose message does not repeat the value. |
| **Redirects and other origins** | Redirects are never followed (`follow_redirects=False`); a 3xx raises `TransportError`. `request()` refuses a path with a scheme or a host. Credentials go to `base_url` only. |
| **TLS** | Verification is httpx's default (on, with certifi's roots); the SDK has no option to turn it off. httpx honours `SSL_CERT_FILE` and `SSL_CERT_DIR`, which replace those roots, and the proxy variables (`HTTPS_PROXY` and others): whoever sets the process environment chooses them. An injected `transport` is the caller's responsibility. |
| **Credentials in the URL** | A `base_url` with user information, a query or a fragment is refused. |
| **Plain-text transport** | `http://` is accepted for loopback development; use `https://` elsewhere, as keys and plaintexts travel in the request. |
| **Malformed responses** | A 2xx body that is not JSON, lacks `data` where the route wraps it, or does not match the method's result type (required members, JSON types, enumerated values) raises `TransportError` naming the member; any error body becomes a `Problem`. Both parsers are fuzzed. |
| **Repeated side effects** | Stateful operations are never retried after a lost connection or a 504. |
| **Slow or oversized responses** | `AsyncClient` bounds each attempt and the whole call in wall-clock time; the blocking `Client` bounds each socket operation, so a server trickling bytes can hold it longer. Bodies are read whole, without a size limit: the server is trusted not to exhaust the caller's memory. |

The [assurance case](docs/ASSURANCE.md) maps these measures to trust
boundaries, secure design principles and CWE entries, with the code and
tests behind each, and the
[2026-11 security review](docs/security-review-2026-11.md) records the
last review and its findings.

### Dependency audit

`make audit` runs pip-audit over every locked dependency in `uv.lock`,
development tools included; CI runs it on every push. Dependabot proposes
weekly updates of `uv.lock` and of the pinned workflow actions.
