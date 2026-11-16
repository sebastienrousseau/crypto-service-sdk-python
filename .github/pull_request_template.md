<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

## What this changes

<!-- What behaviour changes, and why. -->

## How it was verified

<!-- What you ran, and what you observed. Say whether the conformance kit
     ran against a live crypto-server. -->

## Checklist

- [ ] Every commit is signed off (`git commit -s`), see [DCO.txt](../DCO.txt)
- [ ] `make check` passes; `make conformance` passes against crypto-server
- [ ] Tests cover the change
- [ ] `conformance/` is unchanged (it is vendored from crypto-service)
- [ ] `src/crypto_service/_sync/` was regenerated with `make unasync`, not edited
- [ ] Documentation updated if behaviour or interfaces changed
