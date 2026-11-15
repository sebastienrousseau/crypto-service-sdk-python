<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# ADR 0002: httpx with HTTP/2

- Status: accepted
- Date: 2026-11-15

## Context

The SDK needs one HTTP stack for an async and a blocking client, with
connection pooling, keep-alive, HTTP/2, per-request timeouts, no
automatic redirects, TLS verification and a transport seam for tests.

## Decision

httpx (`httpx[http2]`, 0.28 or newer, below 1.0) is the only run-time
dependency. Each SDK client owns one `httpx.AsyncClient` or
`httpx.Client`, created with `http2=True` and `follow_redirects=False`,
and TLS verification left at httpx's default (on). Tests and callers can
pass a `transport`; the SDK's tests use `httpx.MockTransport`.

## Alternatives

- `aiohttp` plus `requests`: two stacks with different timeout and
  error models, and no HTTP/2.
- `urllib3`: blocking only.
- The standard library: no async client, no pooling across threads.

## Consequences

- One error hierarchy to map (`httpx.TimeoutException`,
  `httpx.HTTPError`) and the same behaviour in both clients.
- HTTP/2 is used over TLS when the server offers it through ALPN; plain
  `http://` uses HTTP/1.1 with keep-alive.
- `h2`, `hpack`, `hyperframe`, `httpcore`, `anyio`, `certifi`, `idna`
  and `sniffio` come with httpx.
