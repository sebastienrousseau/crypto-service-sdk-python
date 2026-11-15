#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Everything against a real crypto-server: starts one from a built
# crypto-service checkout on a free loopback port with synthetic
# credentials, runs the gate, the conformance kit, every example, the
# README blocks and a benchmark smoke run, and stops the server even on
# failure.
#
# CRYPTO_SERVICE_SERVER: the checkout (at the commit in ci/server.ref,
# after `pnpm install --frozen-lockfile && pnpm -r run build`).
#
# Usage: CRYPTO_SERVICE_SERVER=/path/to/crypto-service scripts/regression.sh
set -euo pipefail
cd "$(dirname "$0")/.."

server="${CRYPTO_SERVICE_SERVER:?set CRYPTO_SERVICE_SERVER to a built crypto-service checkout}"
entry="$server/packages/crypto-server/dist/index.js"
[ -f "$entry" ] || { echo "regression: $entry is missing; build the server first" >&2; exit 1; }

port="$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
export CRYPTO_SERVICE_URL="http://127.0.0.1:$port"
export CRYPTO_SERVICE_API_KEY="regression-synthetic-key-0123456789"
export CRYPTO_SERVICE_JWT_SECRET="regression-synthetic-jwt-secret-0123456789abcdef"
log="$(mktemp)"

CRYPTO_API_KEY="$CRYPTO_SERVICE_API_KEY" JWT_SECRET="$CRYPTO_SERVICE_JWT_SECRET" \
  PORT="$port" HOST=127.0.0.1 NODE_ENV=development RATE_LIMIT_MAX=100000 \
  node "$entry" > "$log" 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT

for _ in $(seq 1 60); do
  if curl -fsS "$CRYPTO_SERVICE_URL/health" > /dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS "$CRYPTO_SERVICE_URL/health" > /dev/null || { cat "$log"; exit 1; }

make check
make conformance
make examples
make readme
make bench BENCH_ARGS="--benchmark-min-rounds=5 --benchmark-max-time=0.1"
echo "regression: passed against crypto-server at $CRYPTO_SERVICE_URL"
