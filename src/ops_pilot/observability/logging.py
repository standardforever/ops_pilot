"""Minimal structured logging without payload or secret leakage."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from ops_pilot.config import Environment, Settings
from ops_pilot.observability.redaction import redact

LOGGER_NAME = "ops_pilot"
RESERVED_FIELDS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Render one safe JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "service": "ops-pilot",
            "event": record.getMessage(),
        }
        fields.update(
            {key: value for key, value in record.__dict__.items() if key not in RESERVED_FIELDS}
        )
        safe_fields = redact(fields)
        return json.dumps(safe_fields, separators=(",", ":"), default=str)


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure the project logger once per application construction."""

    logger = logging.getLogger(LOGGER_NAME)
    logger.handlers.clear()
    logger.setLevel(settings.log_level)
    logger.propagate = False

    handler = logging.StreamHandler()
    if settings.environment is not Environment.TEST:
        handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
