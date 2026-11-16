# SPDX-License-Identifier: Apache-2.0 OR MIT
# Generated from src/crypto_service/_async/_meta.py by scripts/unasync.py.
# Do not edit: change the async source and run `make unasync`.
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
from ._base import Base


class MetaOps(Base):
    """``GET`` routes that describe the service."""

    def root(self) -> RootInfo:
        """``GET /``: the service description (not wrapped in ``data``)."""
        return cast(RootInfo, self._call("GET", "/", wrapped=False))

    def health(self) -> HealthResult:
        """``GET /health``, a public probe: no credentials are sent."""
        return cast(HealthResult, self._call("GET", "/health", wrapped=False, auth=False))

    def live(self) -> LiveResult:
        """``GET /live``, a public probe: no credentials are sent."""
        return cast(LiveResult, self._call("GET", "/live", wrapped=False, auth=False))

    def ready(self) -> ReadyResult:
        """``GET /ready``, a public probe: no credentials are sent.

        A server that is not ready answers 503, raised as
        :class:`~crypto_service.ApiError` (and retried when retries are on).
        """
        return cast(ReadyResult, self._call("GET", "/ready", wrapped=False, auth=False))

    def algorithms(self) -> AlgorithmCatalogue:
        """``GET /v2/algorithms``: every algorithm name by category."""
        return cast(AlgorithmCatalogue, self._call("GET", "/v2/algorithms"))

    def get_dora_compliance(self) -> DoraCompliance:
        """``GET /v2/compliance/dora``: the DORA Article 9 and 13 self-assessment."""
        return cast(DoraCompliance, self._call("GET", "/v2/compliance/dora"))

    def get_cbom(self) -> Cbom:
        """``GET /v2/compliance/cbom``: the CycloneDX 1.6 CBOM, not wrapped in ``data``."""
        return cast(Cbom, self._call("GET", "/v2/compliance/cbom", wrapped=False))
