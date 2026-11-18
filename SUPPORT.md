<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Getting support

## Read first

- [README.md](README.md): install, quick start, configuration and the
  limits of the SDK.
- [The examples](examples/): runnable programs; CI runs every one against
  a live server.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how a call travels
  through the SDK.
- [DEVELOPMENT.md](DEVELOPMENT.md): setup, testing and every CI gate.

## Supported versions

While pre-`1.0`, the latest released `0.0.x` is supported; older ones
are not. The SDK follows the Crypto Service suite's version, so SDK
0.0.N is tested against crypto-server 0.0.N.

| Version | Status | Supported |
| :--- | :--- | :--- |
| `0.0.41` (latest) | Current | Yes |
| `0.0.40` | Previous | Until 0.0.41 is released |
| `main` | In development | Yes |

## Questions and bugs

Open an [issue](https://github.com/sebastienrousseau/crypto-service-sdk-python/issues/new/choose).
For a bug, include the SDK version, the crypto-server version (`GET /`),
your Python and httpx versions, and a minimal reproducer. Use synthetic
keys and credentials only.

A behaviour that comes from the server (a status, a problem, an
encoding) belongs in [crypto-service's issues](https://github.com/sebastienrousseau/crypto-service/issues).

## Security

Never report a vulnerability in a public issue; follow
[SECURITY.md](SECURITY.md).

## Response times

The project is maintained in a personal capacity, with no SLA. The goal
is a first answer within a few working days.
