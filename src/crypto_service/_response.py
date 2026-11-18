# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""The answer to a raw :meth:`AsyncClient.request` call."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Response:
    """Status, headers and body of a response, whatever its status."""

    status: int
    headers: Mapping[str, str] = field(repr=False)
    content: bytes = field(repr=False)

    @property
    def media_type(self) -> str:
        """``Content-Type`` without parameters, lowercase (empty when absent)."""
        return self.headers.get("content-type", "").split(";")[0].strip().lower()

    def json(self) -> Any:
        """The body parsed as JSON; raises ``ValueError`` when it is not JSON."""
        return json.loads(self.content)
