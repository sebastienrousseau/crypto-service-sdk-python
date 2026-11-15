# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Replay the fuzz seed corpus through the fuzz targets (no atheris needed)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fuzz import targets

CORPUS = Path(__file__).resolve().parents[1] / "fuzz" / "corpus"
CASES = sorted(CORPUS.glob("*/*"))


@pytest.mark.parametrize("path", CASES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_seed_input(path: Path) -> None:
    getattr(targets, path.parent.name)(path.read_bytes())


def test_targets_accept_empty_input() -> None:
    targets.problem(b"")
    targets.response(b"")
