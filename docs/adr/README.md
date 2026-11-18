<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Architecture decision records

| ADR | Decision |
| :--- | :--- |
| [0001](0001-thin-client-over-the-server.md) | A thin client over crypto-server: no cryptography in the SDK |
| [0002](0002-http-stack-httpx.md) | httpx with HTTP/2 as the only run-time dependency |
| [0003](0003-error-model.md) | `ApiError` with an RFC 9457 `Problem`, `TransportError`, one base |
| [0004](0004-async-model.md) | asyncio first; the blocking client generated from it |
