"""Typed audit output boundary."""

import logging
from dataclasses import dataclass, field
from typing import Protocol

from ops_pilot.domain import AuditEvent
from ops_pilot.observability.logging import LOGGER_NAME


class AuditSink(Protocol):
    """Boundary for recording an already validated audit event."""

    def emit(self, event: AuditEvent) -> None:
        """Record the event or raise when required recording fails."""
        ...


@dataclass(slots=True)
class LoggingAuditSink:
    """Emit safe audit metadata through the structured project logger."""

    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(LOGGER_NAME))

    def emit(self, event: AuditEvent) -> None:
        self.logger.info(event.event_name, extra=event.model_dump(mode="json"))


@dataclass(slots=True)
class InMemoryAuditSink:
    """Deterministic test sink; not used as durable storage."""

    events: list[AuditEvent] = field(default_factory=list)

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)
