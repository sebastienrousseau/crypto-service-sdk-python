<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Development

## Setup

```sh
mise install          # Python 3.14, uv 0.13.1, Node 24 (mise.toml)
make sync             # uv sync --frozen: the locked development environment
```

The project is built with hatchling and developed with uv; `uv.lock` is
committed and every `make` target runs with `--frozen`.

## Layout

| Path | What it holds |
| :--- | :--- |
| `src/crypto_service/_core.py` | Options, headers, retry decisions, deadlines, encoding and decoding: everything that does no I/O |
| `src/crypto_service/_problem.py` | RFC 9457 problem parsing |
| `src/crypto_service/_async/` | `AsyncClient`: the pool and send loop (`_base.py`) and one mixin per API area |
| `src/crypto_service/_sync/` | `Client`, generated from `_async/` by `scripts/unasync.py` |
| `src/crypto_service/types.py`, `encoding.py`, `errors.py` | Public types, encoding helpers, exceptions |
| `tests/` | Unit tests (both clients over `httpx.MockTransport`), the kit runner in `tests/support/` |
| `conformance/` | The kit, vendored from crypto-service at `ci/server.ref` |
| `examples/`, `benchmarks/`, `fuzz/` | Runnable examples, pytest-benchmark scenarios, atheris targets |

## CI gates and their local commands

| CI job | What it checks | Local command |
| :--- | :--- | :--- |
| `ci.yml` lint | Version restatements, shellcheck, generated client, ruff, mypy --strict, complexity, pip-audit | `make versions unasync-check lint format-check typecheck complexity audit` |
| `ci.yml` test (3.11 to 3.14) | Unit tests at 100% line and branch coverage | `make coverage` |
| `ci.yml` build | sdist and wheel, `twine check --strict`, a clean install | `make build` |
| `ci.yml` api | Public API against the last tag (griffe) | `uvx --from griffe==2.4.1 griffe check crypto_service --search src --against <tag>` |
| `ci.yml` conformance | The kit, every example, every README block, a benchmark smoke run, against crypto-server built at `ci/server.ref` | `make regression` |
| `fuzz.yml` | atheris, 60 s per target (600 s weekly) | `make fuzz` |
| `codeql.yml` | CodeQL for Python and for the workflows | (GitHub only) |
| `docs-lint.yml` | markdownlint, the README template, codespell, REUSE, links | `scripts/readme-check.sh` and the tools named in the workflow |
| `dco.yml` | `Signed-off-by:` on every commit | `git log --format=%B` |
| `scorecard.yml` | OpenSSF Scorecard | (GitHub only) |

## Coverage

`make coverage` runs the unit tests under coverage.py with branch
coverage and fails below 100% (`fail_under = 100` in `pyproject.toml`).
There are no exclusion markers in `src/`.

## Complexity

`scripts/check_complexity.py` measures every function in `src/`,
`tests/`, `scripts/`, `benchmarks/`, `fuzz/` and `examples/` with radon
(cyclomatic, Halstead difficulty) and complexipy (cognitive), plus
function and file length, against `scripts/complexity-baseline.json`.
The baseline is empty; it can only shrink. Ruff's `C90` rule enforces
the cyclomatic ceiling too.

## The blocking client

`scripts/unasync.py` rewrites each module of `_async/` into `_sync/`
(`async def` to `def`, `await` dropped, `asyncio.sleep` to `time.sleep`,
the `Async` prefix dropped) and formats the result with ruff.
`make unasync` writes it; `make unasync-check` fails when it is stale.
The one behavioural difference: the async client also bounds each
attempt as a whole with `asyncio.timeout`, while the blocking client
relies on httpx's connect, read, write and pool timeouts
([ADR 0004](docs/adr/0004-async-model.md)).

## Conformance

`tests/test_conformance.py` checks the kit's `SHA256SUMS` on every run
and, with `CRYPTO_SERVICE_URL`, `CRYPTO_SERVICE_API_KEY` and
`CRYPTO_SERVICE_JWT_SECRET` set, runs every vector file against that
server. The kit needs the server's JWT secret: each file runs as its own
principal with tokens of chosen scopes, as the kit's README describes.
`make conformance` sets `CRYPTO_SERVICE_REQUIRE_LIVE=1`, which turns a
missing variable into a failure.

## Release model

1. On `feat/v<version>`: move the version in `pyproject.toml` and every
   restatement (`scripts/verify-release-versions`), date the
   `CHANGELOG.md` heading, and write `docs/releases/<version>.md` with a
   `## Highlights` section.
2. Merge the release pull request into `main` once CI is green.
3. Tag `main` with a signed annotated tag:
   `git tag -s v<version> -m "crypto-service-sdk-python v<version>"`, and
   push the tag.
4. `release.yml` checks the tag, runs the gate, builds the sdist and the
   wheel, writes the CycloneDX SBOM and `SHA256SUMS`, attests the build
   provenance, creates the GitHub release titled
   `crypto-service-sdk-python <version>` (Highlights, What's Changed,
   Checksums, Full Changelog), and publishes to PyPI.

PyPI publishing uses trusted publishing: the PyPI project
`crypto-service-sdk-python` trusts this repository's `release.yml` in the
`release` environment. No token is stored. A dry run
(`workflow_dispatch` with `dry-run` on) builds and checks everything and
publishes nothing.
