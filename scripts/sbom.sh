#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
#
# Writes the CycloneDX SBOM of the wheel in dist/ and its run-time
# dependencies, reproducibly: the dependencies come from uv.lock (with
# their hashes), the wheel is installed from dist/ as from an index (so
# no local path is recorded), the environment has no pip, and
# cyclonedx-py omits the serial number and the timestamp. The same
# commit gives the same bytes on any machine. release.yml runs it.
#
# Usage: scripts/sbom.sh OUTPUT.cdx.json
set -euo pipefail
cd "$(dirname "$0")/.."

output="${1:?usage: scripts/sbom.sh OUTPUT.cdx.json}"
version="$(sed -n 's/^version = "\([^"]*\)"$/\1/p' pyproject.toml | head -n 1)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

uv export --frozen --no-dev --no-emit-project --format requirements-txt \
  -o "$scratch/runtime.txt" -q
uv venv -q --python "$(cat .python-version)" "$scratch/runtime"
uv pip install -q --python "$scratch/runtime/bin/python" --require-hashes \
  -r "$scratch/runtime.txt"
uv pip install -q --python "$scratch/runtime/bin/python" --no-deps --no-index \
  --find-links dist "crypto-service-sdk-python==$version"
uv run --frozen --only-group sbom cyclonedx-py environment \
  --mc-type library --output-reproducible --output-format JSON \
  --output-file "$output" "$scratch/runtime/bin/python"
jq -e '[.components[].name | ascii_downcase] | index("httpx")' "$output" > /dev/null
