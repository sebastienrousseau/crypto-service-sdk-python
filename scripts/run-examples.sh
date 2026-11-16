#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Runs every example in examples/ against the server at
# CRYPTO_SERVICE_URL with CRYPTO_SERVICE_API_KEY, and fails when one
# exits non-zero.
#
# Usage: scripts/run-examples.sh
set -euo pipefail
cd "$(dirname "$0")/.."

: "${CRYPTO_SERVICE_URL:?set CRYPTO_SERVICE_URL to a running crypto-server}"
: "${CRYPTO_SERVICE_API_KEY:?set CRYPTO_SERVICE_API_KEY to the CRYPTO_API_KEY of the server}"

status=0
count=0
for example in examples/*.py; do
  count=$((count + 1))
  echo "== $example"
  if ! uv run --frozen python "$example"; then
    echo "run-examples: $example failed" >&2
    status=1
  fi
done
echo "run-examples: $count examples, exit $status"
exit "$status"
