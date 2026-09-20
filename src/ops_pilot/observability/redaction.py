"""Centralized redaction for structured operational data."""

from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = frozenset(
    {
        "authorization",
        "credential",
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
    }
)


def is_sensitive_key(key: str) -> bool:
    """Return whether a field name is likely to carry a credential."""

    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact(value: Any) -> Any:
    """Recursively redact values associated with sensitive field names."""

    if isinstance(value, Mapping):
        return {
            str(key): REDACTED if is_sensitive_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [redact(item) for item in value]
    return value
