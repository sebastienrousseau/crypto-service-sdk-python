<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau -->

# Verifying and reproducing a release

Each GitHub release carries the sdist, the wheel, a CycloneDX SBOM and
`SHA256SUMS`, all built by `release.yml` from a signed tag and covered by
one Sigstore build provenance attestation. PyPI holds the same sdist and
wheel with PEP 740 attestations. This page checks each link of that
chain, then rebuilds the files yourself.

## 1. The tag is signed by a maintainer key

Release tags are SSH-signed annotated tags. [`KEYS.asc`](https://github.com/sebastienrousseau/crypto-service-sdk-python/blob/main/KEYS.asc)
lists the maintainer's public keys in OpenSSH allowed-signers format; its
history is the trust log.

```sh
git clone https://github.com/sebastienrousseau/crypto-service-sdk-python
cd crypto-service-sdk-python
git -c gpg.ssh.allowedSignersFile=KEYS.asc verify-tag v0.0.40
# Good "git" signature for sebastienrousseau@users.noreply.github.com with ED25519 key SHA256:6ikFVl77+...
```

## 2. The files are the ones the workflow built from that tag

Download the release assets and check their digests:

```sh
gh release download v0.0.40 -R sebastienrousseau/crypto-service-sdk-python
sha256sum -c SHA256SUMS
```

Then check each file's build provenance with the GitHub CLI. The command
fails unless a Sigstore attestation for the file's SHA-256 was signed by
`release.yml` in this repository, running on the tag:

```sh
for f in *.whl *.tar.gz *.cdx.json SHA256SUMS; do
  gh attestation verify "$f" \
    --repo sebastienrousseau/crypto-service-sdk-python \
    --signer-workflow sebastienrousseau/crypto-service-sdk-python/.github/workflows/release.yml \
    --source-ref refs/tags/v0.0.40
done
```

A file changed after the build (one byte is enough) has no attestation
and the command exits non-zero.

The files on PyPI carry PEP 740 attestations from the same workflow, by
trusted publishing in the `release` environment. PyPI shows them on each
file's page, and its integrity API returns them:

```sh
curl -s https://pypi.org/integrity/crypto-service-sdk-python/0.0.40/crypto_service_sdk_python-0.0.40-py3-none-any.whl/provenance \
  | jq '.attestation_bundles[0].publisher'
# {"environment": "release", "kind": "GitHub",
#  "repository": "sebastienrousseau/crypto-service-sdk-python", "workflow": "release.yml"}
```

The wheel and sdist on PyPI have the same SHA-256 as in `SHA256SUMS`.

## 3. Rebuild the sdist and the wheel

The build is reproducible: hatchling gives every archive entry a fixed
timestamp, and `uv build` runs it in an isolated environment. The bytes
depend on the hatchling version, which the wheel's `WHEEL` file names
(`Generator: hatchling 1.33.0` for v0.0.40). From 0.0.41,
`pyproject.toml` pins it (`tool.uv.build-constraint-dependencies`); for
v0.0.40, pass the same constraint. With the toolchain in `mise.toml`
(uv 0.13.1):

```sh
git checkout v0.0.40
mise install          # or install uv 0.13.1 yourself
echo 'hatchling==1.33.0' > /tmp/build-constraints.txt
rm -rf dist && uv build --build-constraint /tmp/build-constraints.txt
sha256sum dist/*
```

Expected for v0.0.40, the values in that release's `SHA256SUMS` and on
PyPI:

| File | SHA-256 |
| :--- | :--- |
| `crypto_service_sdk_python-0.0.40-py3-none-any.whl` | `0fa1ed37ca060e1666fb2b2e9c36b9dcfdc69e5149204e436ce7fde2e6545197` |
| `crypto_service_sdk_python-0.0.40.tar.gz` | `1eeec3bd709f5e72dfe80b75965e8101eae61eb9a3569ae2e1e38871d5f9f8e9` |

These were rebuilt twice on 2026-11-18, on Linux with uv 0.13.1 and
hatchling 1.33.0, and matched both times; hatchling 1.29.0 gives other
bytes.

## 4. Rebuild the SBOM (from 0.0.41)

`scripts/sbom.sh` writes the release SBOM from the wheel in `dist/`. It
installs the run-time dependencies from `uv.lock` with their hashes into
an environment without pip, on the Python of `.python-version`, installs
the wheel as from an index so no local path is recorded, and has
cyclonedx-py leave out the serial number and the timestamp:

```sh
scripts/sbom.sh crypto-service-sdk-python-<version>.cdx.json
sha256sum crypto-service-sdk-python-<version>.cdx.json
```

The same commit gives the same bytes in any directory; CI runs it twice
on every pull request and compares them. The v0.0.40 SBOM is not
reproducible: it was written from a `python3 -m venv` environment, so it
records the runner's path to the wheel and the version of pip that
Ubuntu's Python seeded.
