#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Run every fenced code block in README.md, in order, as a user would.

A fresh virtual environment comes first. ``sh`` blocks run under bash
from the repository root with that environment first on ``PATH`` and
``PIP_FIND_LINKS`` pointing at ``dist/``, so the install command
installs the wheel ``make build`` produced (the same version, before it
is on PyPI). ``python`` blocks run with the environment's interpreter
from a scratch directory, so they import the installed package, not
``src/``. A block in any other language fails the run: the README holds
only code that is executed. Python blocks need ``CRYPTO_SERVICE_URL``
and ``CRYPTO_SERVICE_API_KEY``.

Usage: scripts/readme_snippets.py [README.md]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```([A-Za-z0-9_-]*)\n(.*?)^```$", re.MULTILINE | re.DOTALL)


def blocks(text: str) -> list[tuple[str, str]]:
    """Every fenced block as (language, code)."""
    return [(match.group(1), match.group(2)) for match in FENCE.finditer(text)]


def run_block(number: int, language: str, code: str, env: dict[str, str], scratch: Path) -> int:
    print(f"== block {number} ({language})", flush=True)
    if language == "sh":
        command = ["bash", "-euo", "pipefail", "-c", code]
        return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode
    if language == "python":
        script = scratch / f"block_{number}.py"
        script.write_text(code, encoding="utf-8")
        python = str(scratch / "venv" / "bin" / "python")
        return subprocess.run([python, str(script)], cwd=scratch, env=env, check=False).returncode
    print(f"readme-snippets: block {number} is {language or 'untagged'}; use sh or python")
    return 1


def main(argv: list[str]) -> int:
    readme = Path(argv[1]) if len(argv) > 1 else ROOT / "README.md"
    found = blocks(readme.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="readme-snippets-") as tmp:
        scratch = Path(tmp)
        venv.create(scratch / "venv", with_pip=True)
        env = dict(os.environ)
        env.pop("VIRTUAL_ENV", None)  # uv in `make` blocks keeps the project's .venv
        env["PATH"] = f"{scratch / 'venv' / 'bin'}{os.pathsep}{env['PATH']}"
        env["PIP_FIND_LINKS"] = str(ROOT / "dist")
        env.pop("PYTHONPATH", None)
        failed = [
            number
            for number, (language, code) in enumerate(found, 1)
            if run_block(number, language, code, env, scratch) != 0
        ]
    print(f"readme-snippets: {len(found) - len(failed)}/{len(found)} blocks passed")
    return 1 if failed or not found else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
