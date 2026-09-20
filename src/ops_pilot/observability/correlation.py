"""Correlation identifier validation and generation."""

import re
from uuid import uuid4

CORRELATION_HEADER = "X-Correlation-ID"
CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def normalize_correlation_id(candidate: str | None) -> str:
    """Preserve a safe caller identifier or generate an opaque replacement."""

    if candidate and CORRELATION_PATTERN.fullmatch(candidate):
        return candidate
    return f"corr-{uuid4().hex}"
