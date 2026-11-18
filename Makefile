# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
#
# `make check` is the gate: version restatements, the generated blocking
# client, ruff (lint and format), mypy --strict, the complexity ceilings,
# and the unit tests at 100% line and branch coverage. Everything runs
# through uv in the locked environment (`uv sync` first; `make` does it).
#
# The live targets (conformance, examples, readme, bench round trip) need
# a crypto-server: CRYPTO_SERVICE_URL and CRYPTO_SERVICE_API_KEY, plus
# CRYPTO_SERVICE_JWT_SECRET for the kit. `make regression` starts one
# from a crypto-service checkout (CRYPTO_SERVICE_SERVER) and runs them all.

UV           ?= uv
RUN           = $(UV) run --frozen
PYTHON_FUZZ  ?= 3.12
FUZZ_SECONDS ?= 60
FUZZ_TARGETS  = problem response
BENCH_ARGS   ?=
PORT         ?= 3106

.PHONY: check sync versions unasync unasync-check lint format format-check typecheck \
  complexity test coverage conformance examples readme bench fuzz audit build docs demo \
  regression clean

check: sync versions unasync-check lint format-check typecheck complexity coverage

sync:
	$(UV) sync --frozen --all-groups

versions:
	./scripts/verify-release-versions
	./scripts/verify-release-versions-test.sh

# Regenerate src/crypto_service/_sync from the async source.
unasync:
	$(RUN) python scripts/unasync.py

unasync-check:
	$(RUN) python scripts/unasync.py --check

lint:
	$(RUN) ruff check .

format:
	$(RUN) ruff check --fix --select I .
	$(RUN) ruff format .

format-check:
	$(RUN) ruff format --check .

typecheck:
	$(RUN) mypy

# Cyclomatic 10, cognitive 15, Halstead difficulty 30, 60 lines per
# function, 500 lines per file (radon and complexipy), against
# scripts/complexity-baseline.json, which is empty.
complexity:
	$(RUN) python scripts/check_complexity.py

test:
	$(RUN) pytest

# The unit tests alone (no server), gated at 100% line and branch.
coverage:
	env -u CRYPTO_SERVICE_URL -u CRYPTO_SERVICE_REQUIRE_LIVE $(RUN) coverage run -m pytest
	$(RUN) coverage report
	$(RUN) coverage xml -q

# The kit against a live server; fails (not skips) without one.
conformance:
	CRYPTO_SERVICE_REQUIRE_LIVE=1 $(RUN) pytest -m conformance tests/test_conformance.py -v

examples:
	./scripts/run-examples.sh

# Every fenced code block in README.md, in a fresh virtual environment
# that installs the wheel from dist/ (scripts/readme_snippets.py).
readme: build
	$(RUN) python scripts/readme_snippets.py

# pytest-benchmark. round_trip_hash needs CRYPTO_SERVICE_URL. CI passes
# a short BENCH_ARGS to smoke-run them; nothing is asserted.
bench:
	$(RUN) pytest benchmarks -o testpaths=benchmarks --benchmark-only \
	  --benchmark-columns=min,median,mean,max,rounds $(BENCH_ARGS)

# atheris (libFuzzer) on Python $(PYTHON_FUZZ), FUZZ_SECONDS per target.
# New inputs go to fuzz/corpus-out, crash reproducers to fuzz/artifacts.
fuzz:
	@mkdir -p fuzz/artifacts
	@for target in $(FUZZ_TARGETS); do \
	  mkdir -p fuzz/corpus-out/$$target; \
	  echo "== fuzz_$$target for $(FUZZ_SECONDS)s"; \
	  $(UV) run --isolated --python $(PYTHON_FUZZ) --with atheris \
	    python fuzz/fuzz_$$target.py -max_total_time=$(FUZZ_SECONDS) \
	    -artifact_prefix=fuzz/artifacts/$$target- -print_final_stats=1 \
	    fuzz/corpus-out/$$target fuzz/corpus/$$target || exit 1; \
	done

# pip-audit over every locked dependency, development tools included.
audit:
	$(UV) export --frozen --all-groups --no-emit-project --format requirements-txt \
	  -o .audit-requirements.txt -q
	$(RUN) pip-audit --strict --require-hashes --disable-pip -r .audit-requirements.txt
	rm -f .audit-requirements.txt

build:
	rm -rf dist
	$(UV) build
	$(RUN) twine check --strict dist/*

docs:
	$(UV) run --frozen --group docs mkdocs build --strict

# Render .github/demo.gif with vhs against a server on 127.0.0.1:$(PORT).
demo:
	@command -v vhs >/dev/null 2>&1 || { echo "demo: vhs not found (https://github.com/charmbracelet/vhs)"; exit 1; }
	vhs .github/demo.tape

regression:
	./scripts/regression.sh

clean:
	rm -rf dist build site htmlcov .coverage coverage.xml .benchmarks fuzz/corpus-out fuzz/artifacts
