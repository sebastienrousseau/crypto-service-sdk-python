# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""atheris entry point: the success-response decoder and status mapping.

Run: python fuzz/fuzz_response.py -max_total_time=60 fuzz/corpus/response
"""

from __future__ import annotations

import sys
from pathlib import Path

import atheris

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

with atheris.instrument_imports():
    from fuzz.targets import response

if __name__ == "__main__":
    atheris.Setup(sys.argv, response)
    atheris.Fuzz()
