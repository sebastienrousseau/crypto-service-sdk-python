<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package is a thin, typed Python client for the
crypto-server REST API. Cryptography belongs in the server
([`crypto-service`](https://github.com/sebastienrousseau/crypto-service));
a change here should make the client more correct, safer or easier to
use.

## Before you open a pull request

Everything CI checks, you can run locally (`mise install` provides
Python and uv):

```sh
make check            # versions, generated client, ruff, mypy --strict, complexity, 100% coverage
```

To run the conformance kit, start a crypto-server built at the commit in
`ci/server.ref` with an API key and a JWT secret, and point the tests at
it:

```sh
cd /path/to/crypto-service/packages/crypto-server
CRYPTO_API_KEY=local-synthetic-key JWT_SECRET=local-synthetic-jwt-secret-0123456789abcdef \
  PORT=3106 HOST=127.0.0.1 NODE_ENV=development RATE_LIMIT_MAX=100000 node dist/index.js &
cd -
export CRYPTO_SERVICE_URL=http://127.0.0.1:3106
export CRYPTO_SERVICE_API_KEY=local-synthetic-key
export CRYPTO_SERVICE_JWT_SECRET=local-synthetic-jwt-secret-0123456789abcdef
make conformance examples readme
```

`make conformance` fails if any vector is skipped, so a run without a
server cannot pass by accident. `make regression` does all of this with
a server it starts and stops. Use synthetic keys and credentials only.

`make fuzz` runs the atheris targets in `fuzz/` (Python 3.12, through
`uv run --isolated`). A reproducer lands in `fuzz/artifacts/`. Add an
input that found a bug to `fuzz/corpus/<target>/` with the fix, and a
unit test for it.

## The README demo

`make demo` renders `.github/demo.gif` from `.github/demo.tape` with
[VHS](https://github.com/charmbracelet/vhs) (it needs `vhs`, `ttyd` and
`ffmpeg`) against a server on 127.0.0.1:3106 with
`CRYPTO_SERVICE_URL` and `CRYPTO_SERVICE_API_KEY` set. Re-render the GIF
in the same change as anything that alters what it shows.

## Rules

- **`conformance/` is vendored from crypto-service.** Never edit it here;
  the checksum test fails on any local edit.
- **Edit `src/crypto_service/_async/`, not `_sync/`.** Run
  `make unasync` to regenerate the blocking client.
- **Complexity ceilings.** Every function stays within cyclomatic 10,
  cognitive 15, Halstead difficulty 30 and 60 lines, and every file
  within 500 lines (`make complexity`).
- **100% coverage.** `make coverage` fails below 100% of lines and
  branches in `src/`; add the test with the code.
- **No suppressions.** Fix the cause rather than adding `noqa` or
  `type: ignore`; a justified exception is a specific inline code with a
  reason.
- **Tests with the change**, in the same commit.
- **Never log or expose** credentials, keys, plaintexts, bodies or
  problem details from library code.

## Commits

Conventional commits (`feat:`, `fix:`, `docs:`, `ci:`, `test:`,
`chore:`), an imperative subject of at most 50 characters, and a body
wrapped at 72 characters that explains what and why. Every commit
carries a `Signed-off-by:` trailer (`git commit -s`), which certifies
the [DCO](DCO.txt), and is signed.

## Versioning

The version lives in `pyproject.toml` and is restated in the files
`scripts/verify-release-versions` lists; `make check` and CI run it.
**Versions increment by 0.0.1**, in lockstep with the suite.
[DEVELOPMENT.md](DEVELOPMENT.md) describes the release model.

## Licence

Apache-2.0 OR MIT, at your option. By contributing you agree your work is
released under the same dual grant.
