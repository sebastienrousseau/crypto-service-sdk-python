<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Architecture

## One call

```text
client.hash(algorithm="sha256", data="abc")          # _async/_digest.py
  -> body {"algorithm": "sha256", "data": "abc"}      # bytes arguments hex- or base64-encoded
  -> AsyncBase._call("POST", "/v2/hash", body)        # _async/_base.py
       encode_body, Config.headers                     # _core.py: JSON, User-Agent, credentials, traceparent
       _send: loop over attempts                       # Deadline, delay_after_error / delay_after_status
         _attempt: asyncio.timeout(budget) + httpx     # one pooled httpx.AsyncClient per SDK client
       decode_response(status, reason, content)        # 3xx -> TransportError, 4xx/5xx -> ApiError(Problem), 2xx -> data
  <- {"digest": "...", "algorithm": "sha256", "length": 32}
```

## Modules

| Module | Role |
| :--- | :--- |
| `_core` | Sans-I/O rules: `Config` (validated, immutable, redacted `repr`), headers, the retry-safety table, backoff with full jitter, `Retry-After`, `Deadline`, JSON encoding and decoding |
| `_problem` | Any error body to a `Problem`; non-problems become `about:blank` |
| `_async/_base` | `AsyncBase`: the httpx pool, the attempt loop, `request()` |
| `_async/_meta`, `_digest`, `_symmetric`, `_keys`, `_pq`, `_sealed`, `_kms`, `_opaque` | One mixin per API area; each method builds a body and calls `_call` |
| `_async/_client` | `AsyncClient`, the union of the mixins |
| `_sync/*` | The same, generated: `Client` |
| `types`, `encoding`, `errors` | Public types, encoding helpers, exceptions |

Every rule that does not touch the network is in `_core` and
`_problem`, so the two clients share it and it is tested once.

## Concurrency

- `AsyncClient` holds one `httpx.AsyncClient`: share it between tasks on
  the event loop that uses it. Its configuration is immutable after
  construction; each call keeps its own state (attempt count, deadline,
  traceparent).
- `Client` holds one `httpx.Client`, whose connection pool is guarded by
  locks: one instance can be shared between threads.
- Cancelling the task that awaits a call cancels the HTTP request
  (`asyncio.CancelledError` propagates; the SDK never swallows it).

## Retries

| Answer | Idempotent or pure operation | Stateful operation |
| :--- | :--- | :--- |
| 429, 503 | Retried | Retried |
| 504 | Retried | Not retried |
| No response (connection error, timeout) | Retried | Not retried |
| Any other status | Not retried | Not retried |

Stateful: `/v2/keys/generate`, `/v2/keys/delete`, every `*/keygen`,
`/v2/kms/create-key`, `/v2/opaque/register/*`, the table of the
TypeScript SDK's `request.ts`. Retries are off unless `retry` sets
`max_retries`.
