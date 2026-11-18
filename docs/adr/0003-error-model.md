<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# ADR 0003: Error model

- Status: accepted
- Date: 2026-11-15

## Context

crypto-server answers every error with an RFC 9457 problem
(`application/problem+json`): `type` (`urn:crypto-service:problem:<slug>`),
`title`, `status`, `detail`, `instance`, and extension members such as
`code` and `errors[]`. Proxies in front of it may answer with HTML or
nothing. The suite's SDK contract names `ApiError` and `TransportError`
with one base.

## Decision

- `CryptoServiceError` is the base of every SDK exception.
- `ApiError` is raised for a 4xx or 5xx answer. Its `problem` is a
  frozen `Problem` with the fields above, `errors` as a tuple of
  `ValidationIssue(field, message)`, and `raw`, the whole document with
  its extension members. A body that is not JSON, or has no string
  `detail`, becomes an `about:blank` problem with the response's status
  and reason. `status` is always the HTTP status of the response.
- `TransportError` is raised when no usable response arrived: a
  connection error, a timeout (`timed_out=True`), the call's deadline
  passing (`timed_out=True`), a redirect (refused), or a 2xx body that
  cannot be decoded. The underlying exception is `__cause__`.
- Bad options raise `ValueError` at construction.
- Messages and `repr` carry the status, the problem type and the title
  only. `detail` can echo request data, so it is reachable as an
  attribute and never formatted into a message.

## Consequences

- One `except ApiError` handles every server-side failure; the problem
  type and `code` are stable to branch on.
- Logging an exception does not leak request data or credentials.
- A redirect or an undecodable success is a `TransportError`, which the
  suite contract describes as "no response"; the SDK treats a response
  it refuses to use the same way, and never retries it.
