<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

No figures are published yet. This page describes the scenarios and the
method; results will be generated into it with the hardware, Python
version and server commit they were measured on.

## Scenarios

The same names in every Crypto Service SDK:

| Scenario | Measures | Network |
| :--- | :--- | :--- |
| `encode_request` | A `/v2/hash` body as JSON bytes and the request headers | None |
| `decode_response` | A recorded `/v2/hash` 200 response to its `data` | None |
| `decode_problem` | A recorded `validation-failed` 400 to a `Problem` | None |
| `round_trip_hash` | `Client.hash` against a local crypto-server, connection warm | Loopback |

The recorded responses are in `benchmarks/responses/`, captured from
crypto-server at the commit in `ci/server.ref`.

## Method

pytest-benchmark (`make bench`), on an idle machine, with the default
calibration for the client-side scenarios and a fixed number of rounds
(`CRYPTO_SERVICE_BENCH_ROUNDS`, default 20) for the round trip, which
runs only when `CRYPTO_SERVICE_URL` is set. The server meters each
principal (60 requests a minute by default), so the round trip retries
429 answers; a run long enough to hit the quota measures the quota, not
the client. CI smoke-runs every scenario and asserts nothing about
speed.
