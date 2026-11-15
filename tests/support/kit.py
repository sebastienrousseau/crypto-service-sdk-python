# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Loading and matching the vendored conformance kit (conformance/README.md).

Templates match exactly, except an object whose only member is
``$shape``, which matches any value its JSON Schema (2020-12) accepts.
``${name}`` in any string is replaced with a value captured earlier in
the same file, through ``capture`` (a JSON pointer into a response).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

KIT = Path(__file__).resolve().parents[2] / "conformance"
_PLACEHOLDER = re.compile(r"\$\{([A-Za-z0-9_]+)\}")


def kit_files() -> list[tuple[str, dict[str, Any]]]:
    """Every vector file, by name, in sorted order."""
    return [
        (path.name, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(KIT.glob("*.json"))
    ]


def checksum_mismatches() -> list[str]:
    """Files whose SHA-256 differs from SHA256SUMS, or that it does not list."""
    listed: dict[str, str] = {}
    for line in (KIT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        listed[name.lstrip("*")] = digest
    present = {p.name for p in KIT.iterdir() if p.name != "SHA256SUMS"}
    problems = [f"{name}: not listed" for name in sorted(present - set(listed))]
    problems += [f"{name}: listed but missing" for name in sorted(set(listed) - present)]
    for name in sorted(present & set(listed)):
        actual = hashlib.sha256((KIT / name).read_bytes()).hexdigest()
        if actual != listed[name]:
            problems.append(f"{name}: digest {actual} != {listed[name]}")
    return problems


def substitute(value: Any, captured: dict[str, str]) -> Any:
    """``value`` with every ``${name}`` replaced by its captured string."""
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda m: captured[m.group(1)], value)
    if isinstance(value, list):
        return [substitute(item, captured) for item in value]
    if isinstance(value, dict):
        return {key: substitute(item, captured) for key, item in value.items()}
    return value


def pointer(document: Any, path: str) -> Any:
    """Resolve an RFC 6901 JSON pointer."""
    for raw in path.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        document = document[int(token)] if isinstance(document, list) else document[token]
    return document


def mismatches(template: Any, actual: Any, at: str = "") -> list[str]:
    """Where ``actual`` differs from the template; empty when it matches."""
    if isinstance(template, dict) and set(template) == {"$shape"}:
        errors = Draft202012Validator(template["$shape"]).iter_errors(actual)
        return [f"{at or '/'}: {error.message}" for error in errors]
    if isinstance(template, dict):
        return _object_mismatches(template, actual, at)
    if isinstance(template, list):
        return _list_mismatches(template, actual, at)
    return _scalar_mismatches(template, actual, at)


def _scalar_mismatches(template: Any, actual: Any, at: str) -> list[str]:
    same = type(template) is type(actual) or _numbers(template, actual)
    return [] if same and template == actual else [f"{at or '/'}: {actual!r} != {template!r}"]


def _object_mismatches(template: dict[str, Any], actual: Any, at: str) -> list[str]:
    if not isinstance(actual, dict) or set(actual) != set(template):
        return [f"{at or '/'}: members {_keys(actual)} != {sorted(template)}"]
    found: list[str] = []
    for key, expected in template.items():
        found += mismatches(expected, actual[key], f"{at}/{key}")
    return found


def _list_mismatches(template: list[Any], actual: Any, at: str) -> list[str]:
    if not isinstance(actual, list) or len(actual) != len(template):
        return [f"{at or '/'}: expected a list of {len(template)}"]
    found: list[str] = []
    for index, expected in enumerate(template):
        found += mismatches(expected, actual[index], f"{at}/{index}")
    return found


def _keys(value: Any) -> list[str] | str:
    return sorted(value) if isinstance(value, dict) else type(value).__name__


def _numbers(a: Any, b: Any) -> bool:
    def number(value: Any) -> bool:
        return isinstance(value, int | float) and not isinstance(value, bool)

    return number(a) and number(b)
