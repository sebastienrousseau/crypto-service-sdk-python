<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Governance

How crypto-service-sdk-python is run, who decides, and what happens if
the maintainer is unavailable.

## Scope

The SDK is the Python client for the crypto-server REST API. It carries
no cryptography ([ADR 0001](docs/adr/0001-thin-client-over-the-server.md));
changes are weighed against that: correctness against the conformance
kit, security and clarity over feature breadth.

## Roles

| Role | Who | Responsibilities |
| :--- | :--- | :--- |
| **Maintainer** | Sebastien Rousseau (single maintainer) | Reviews and merges pull requests, cuts and signs releases, triages issues and security reports, sets direction, holds the repository's admin rights |
| **Contributor** | Anyone with a merged pull request | Proposes changes with tests, reviews others' pull requests |
| **User** | Everyone | Reports bugs, asks questions, requests features through issues |

## Decisions

- **Day-to-day changes** (fixes, tests, docs, additive features within
  scope) go through a pull request into the release branch
  `feat/v<next-version>`; the maintainer merges once CI is green.
- **Significant changes** (a breaking change to the public API, a new
  dependency, a change to the version line or the conformance kit)
  start as an issue and get an ADR in `docs/adr/`.
- **The suite version** is decided for the whole Crypto Service family:
  this SDK moves in lockstep with crypto-service, one `0.0.1` step at a
  time.

Every change passes the CI gates (lint, types, complexity, 100% line and
branch coverage on Python 3.11 to 3.14, the conformance kit against a
live server, fuzzing, CodeQL, the DCO check) before merge. At most one
pull request targets `main` at a time: the release branch.

## Releases

Releases follow the process in [DEVELOPMENT.md](DEVELOPMENT.md#release-model):
a signed annotated `v<version>` tag triggers the release workflow. Only
the maintainer pushes tags.

## Access continuity

- **Code and history** are public on GitHub; anyone can fork and build
  from them. Every commit and tag is signed.
- **No secret is needed to build or test.** PyPI publishing uses trusted
  publishing (OIDC) from the `release` environment, with no stored token.
- **If the maintainer is unreachable** for 90 days, the project should
  be treated as unmaintained: users should pin a release, and a fork may
  continue it under a new name. Adding a second maintainer is a standing
  goal.

## Code of conduct

Everyone in the project follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
