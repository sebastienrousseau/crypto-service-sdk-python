<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# ADR 0004: asyncio first, the blocking client generated

- Status: accepted
- Date: 2026-11-15

## Context

The suite's contract makes async the primary API, with a blocking API
beside it where the language has one. Hand-writing 64 methods twice
invites drift; a blocking wrapper around the async client (running an
event loop per call) breaks inside running loops and costs a loop per
call.

## Decision

- `AsyncClient` (asyncio) is the source. `Client` is generated from it by
  `scripts/unasync.py`, a token rewrite (`async def` to `def`, `await`
  dropped, `asyncio.sleep` to `time.sleep`, the `Async` prefix dropped)
  followed by ruff format. The generated files are committed, and
  `make unasync-check` fails CI when they are stale.
- Everything that does no I/O (options, headers, retry decisions,
  deadlines, encoding, decoding, problems) lives in `_core` and
  `_problem`, shared by both.
- Cancellation is asyncio task cancellation: cancelling the awaiting
  task cancels the request, and `CancelledError` is never caught.
- `timeout` is per attempt. The async client enforces it on the whole
  attempt with `asyncio.timeout` as well as through httpx; the blocking
  client relies on httpx's connect, read, write and pool timeouts, each
  bounded by it. `deadline` bounds a whole call in both: each attempt's
  budget is the smaller of `timeout` and the time left, and no retry
  waits past it.

## Consequences

- Both clients have identical methods, retries and errors, tested by
  one suite that runs each test on both.
- A slow server that keeps sending bytes can hold a blocking attempt
  longer than `timeout` (each read is bounded, the sum is not); the
  `deadline` does not interrupt a blocking read either. The async client
  has no such gap.
- An `AsyncClient` is used from the event loop that runs it; threads use
  `Client`.
