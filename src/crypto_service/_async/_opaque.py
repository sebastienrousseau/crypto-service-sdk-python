# SPDX-License-Identifier: Apache-2.0 OR MIT
"""OPAQUE (RFC 9807) registration and login, server side of the exchange.

The client side of OPAQUE (blinding, KE1, KE3) is cryptography this SDK
does not implement: these methods carry the messages an OPAQUE client
library produced.
"""

from __future__ import annotations

from typing import cast

from .._core import compact
from ..encoding import Hex, to_hex
from ..types import (
    OpaqueLoginFinishResult,
    OpaqueLoginInitResult,
    OpaqueRegisterFinishResult,
    OpaqueRegisterInitResult,
    OpaqueSuite,
)
from ._base import AsyncBase


class AsyncOpaqueOps(AsyncBase):
    """Registration needs credentials; login does not."""

    async def opaque_register_init(
        self, *, credential_identifier: str, request: Hex, suite: OpaqueSuite | None = None
    ) -> OpaqueRegisterInitResult:
        """``POST /v2/opaque/register/init`` (stateful)."""
        body = compact(
            {
                "credentialIdentifier": credential_identifier,
                "request": to_hex(request),
                "suite": suite,
            }
        )
        path = "/v2/opaque/register/init"
        return cast(OpaqueRegisterInitResult, await self._call("POST", path, body))

    async def opaque_register_finish(
        self, *, credential_identifier: str, record: Hex, suite: OpaqueSuite | None = None
    ) -> OpaqueRegisterFinishResult:
        """``POST /v2/opaque/register/finish`` (stateful)."""
        body = compact(
            {
                "credentialIdentifier": credential_identifier,
                "record": to_hex(record),
                "suite": suite,
            }
        )
        path = "/v2/opaque/register/finish"
        return cast(OpaqueRegisterFinishResult, await self._call("POST", path, body))

    async def opaque_login_init(
        self, *, credential_identifier: str, ke1: Hex, suite: OpaqueSuite | None = None
    ) -> OpaqueLoginInitResult:
        """``POST /v2/opaque/login/init``: a public route, no credentials are sent."""
        body = compact(
            {"credentialIdentifier": credential_identifier, "ke1": to_hex(ke1), "suite": suite}
        )
        path = "/v2/opaque/login/init"
        return cast(OpaqueLoginInitResult, await self._call("POST", path, body, auth=False))

    async def opaque_login_finish(self, *, session_id: str, ke3: Hex) -> OpaqueLoginFinishResult:
        """``POST /v2/opaque/login/finish``: a public route, no credentials are sent."""
        body = {"sessionId": session_id, "ke3": to_hex(ke3)}
        path = "/v2/opaque/login/finish"
        return cast(OpaqueLoginFinishResult, await self._call("POST", path, body, auth=False))
