# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""Service description, probes, the algorithm catalogue and compliance documents."""

from __future__ import annotations

from typing import cast

from ..types import (
    AlgorithmCatalogue,
    Cbom,
    DoraCompliance,
    HealthResult,
    LiveResult,
    ReadyResult,
    RootInfo,
)
from ._base import AsyncBase


class AsyncMetaOps(AsyncBase):
    """``GET`` routes that describe the service."""

    async def root(self) -> RootInfo:
        """``GET /``: the service description (not wrapped in ``data``)."""
        return cast(RootInfo, await self._call("GET", "/", wrapped=False, expect=RootInfo))

    async def health(self) -> HealthResult:
        """``GET /health``, a public probe: no credentials are sent."""
        return cast(
            HealthResult,
            await self._call("GET", "/health", wrapped=False, auth=False, expect=HealthResult),
        )

    async def live(self) -> LiveResult:
        """``GET /live``, a public probe: no credentials are sent."""
        return cast(
            LiveResult,
            await self._call("GET", "/live", wrapped=False, auth=False, expect=LiveResult),
        )

    async def ready(self) -> ReadyResult:
        """``GET /ready``, a public probe: no credentials are sent.

        A server that is not ready answers 503, raised as
        :class:`~crypto_service.ApiError` (and retried when retries are on).
        """
        return cast(
            ReadyResult,
            await self._call("GET", "/ready", wrapped=False, auth=False, expect=ReadyResult),
        )

    async def algorithms(self) -> AlgorithmCatalogue:
        """``GET /v2/algorithms``: every algorithm name by category."""
        return cast(
            AlgorithmCatalogue, await self._call("GET", "/v2/algorithms", expect=AlgorithmCatalogue)
        )

    async def get_dora_compliance(self) -> DoraCompliance:
        """``GET /v2/compliance/dora``: the DORA Article 9 and 13 self-assessment."""
        return cast(
            DoraCompliance, await self._call("GET", "/v2/compliance/dora", expect=DoraCompliance)
        )

    async def get_cbom(self) -> Cbom:
        """``GET /v2/compliance/cbom``: the CycloneDX 1.6 CBOM, not wrapped in ``data``."""
        return cast(
            Cbom, await self._call("GET", "/v2/compliance/cbom", wrapped=False, expect=Cbom)
        )
