<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Policies

## Toolchain

- **Python floor: 3.11.** CI tests every supported CPython from the floor
  to the newest (3.11, 3.12, 3.13, 3.14). The floor rises only when that
  version reaches its end of life, in a release whose changelog says so.
- **httpx** 0.28 or newer, below 1.0; HTTP/2 through its `http2` extra.
- Development tools are locked in `uv.lock` and updated weekly by
  Dependabot.

## Versioning

Lockstep with the Crypto Service suite, in `0.0.1` steps. SDK 0.0.N is
tested against crypto-server 0.0.N.

## Deprecation

A public name is deprecated for at least one release (with a
`DeprecationWarning` and a changelog entry) before it is removed.

## Supported versions

The latest release and `main`; see [SECURITY.md](https://github.com/sebastienrousseau/crypto-service-sdk-python/blob/main/SECURITY.md).
