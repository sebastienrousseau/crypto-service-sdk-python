# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""atheris entry point: the RFC 9457 problem-body parser.

Run: python fuzz/fuzz_problem.py -max_total_time=60 fuzz/corpus/problem
"""

from __future__ import annotations

import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

with atheris.instrument_imports():
    from fuzz.targets import problem

if __name__ == "__main__":
    atheris.Setup(sys.argv, problem)
    atheris.Fuzz()
