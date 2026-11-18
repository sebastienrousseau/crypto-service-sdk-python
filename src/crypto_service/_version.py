# SPDX-License-Identifier: Apache-2.0 OR MIT
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau
"""The package version, read from the installed distribution metadata.

``pyproject.toml`` is the single source of truth; nothing else restates
the number in code, so the version and the User-Agent cannot drift.
"""

from importlib.metadata import version

__version__: str = version("crypto-service-sdk-python")
USER_AGENT: str = f"crypto-service-sdk-python/{__version__}"
