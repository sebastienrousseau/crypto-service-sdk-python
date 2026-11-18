<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Roadmap

Direction, not commitments. Each item is weighed against the thin-client
rule ([ADR 0001](adr/0001-thin-client-over-the-server.md)).

## Next

- Publish benchmark results in [BENCHMARKS.md](BENCHMARKS.md) with the
  hardware they ran on.
- Render the README demo (`make demo`) once VHS is part of the release
  checklist.
- Track each crypto-server release: re-vendor the kit, move
  `ci/server.ref` to the release tag.

## Later

- Optional OpenTelemetry spans around each call, behind an extra, so the
  base install keeps one dependency.
- Response models with `bytes` accessors for the hex and base64 members,
  if users ask for them beyond `crypto_service.encoding`.

## Not planned

- Local cryptography of any kind.
- Typed methods for the deprecated v1 routes or `/metrics`.
