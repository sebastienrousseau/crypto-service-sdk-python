#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Generate the blocking client (src/crypto_service/_sync) from the async one.

Each module in ``_async`` is rewritten token by token (``async def`` to
``def``, ``await`` dropped, ``asyncio.sleep`` to ``time.sleep``, the
``Async`` class prefix dropped, and so on), then formatted with ruff.
The generated files are committed; ``--check`` fails when one differs
from what this script would write, so the two clients cannot drift.

Usage: scripts/unasync.py [--check]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "crypto_service" / "_async"
TARGET = ROOT / "src" / "crypto_service" / "_sync"

#: Ordered (pattern, replacement) pairs; the order matters.
RULES: tuple[tuple[str, str], ...] = (
    (r"\bimport asyncio\b", "import time"),
    (r"\basyncio\.sleep\b", "time.sleep"),
    (r"\basyncio\.timeout\b", "_core.blocking_scope"),
    (r"\basync def\b", "def"),
    (r"\basync with\b", "with"),
    (r"\bawait ", ""),
    (r"\b__aenter__\b", "__enter__"),
    (r"\b__aexit__\b", "__exit__"),
    (r"\baclose\b", "close"),
    (r"\bAsync(?=[A-Z])", ""),
    (r"\basynchronous\b", "blocking"),
    (r"\bAsynchronous\b", "Blocking"),
    (r"\bevent loop\b", "process"),
    (r"\btasks on one\b", "threads in one"),
    (r"\b_async\b", "_sync"),
)


def header(name: str) -> str:
    return (
        # Split so REUSE does not read this literal as this file's licence.
        "# SPDX"
        "-License-Identifier: Apache-2.0 OR MIT\n"
        f"# Generated from src/crypto_service/_async/{name} by scripts/unasync.py.\n"
        "# Do not edit: change the async source and run `make unasync`.\n"
    )


def transform(name: str, text: str) -> str:
    body = text.split("\n", 1)[1]  # drop the SPDX line; the header restates it
    for pattern, replacement in RULES:
        body = re.sub(pattern, replacement, body)
    return header(name) + body


def formatted(path: Path, text: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--stdin-filename", str(path), "-"],
        input=text,
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return result.stdout


def expected() -> dict[Path, str]:
    return {
        TARGET / source.name: formatted(
            TARGET / source.name, transform(source.name, source.read_text(encoding="utf-8"))
        )
        for source in sorted(SOURCE.glob("*.py"))
    }


def differences(files: dict[Path, str]) -> tuple[list[str], list[str]]:
    """Generated files that differ from disk, and files on disk not generated."""
    stale = sorted(
        path.relative_to(ROOT).as_posix()
        for path, text in files.items()
        if not path.exists() or path.read_text(encoding="utf-8") != text
    )
    extra = sorted(
        path.relative_to(ROOT).as_posix() for path in TARGET.glob("*.py") if path not in files
    )
    return stale, extra


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when _sync is stale")
    args = parser.parse_args(argv)
    files = expected()
    stale, extra = differences(files)
    if args.check:
        for name in stale + extra:
            print(f"unasync: {name} is stale; run `make unasync`", file=sys.stderr)
        return 1 if stale or extra else 0
    TARGET.mkdir(exist_ok=True)
    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    for name in extra:
        (ROOT / name).unlink()
    print(f"unasync: wrote {len(files)} files to {TARGET.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
