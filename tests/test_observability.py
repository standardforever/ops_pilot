"""Correlation, structured logging, audit, and redaction behavior."""

import json
import logging

from fastapi.testclient import TestClient

from ops_pilot.application import create_app
from ops_pilot.config import Environment, Settings
from ops_pilot.observability import CORRELATION_HEADER, InMemoryAuditSink
from ops_pilot.observability.logging import JsonFormatter
from ops_pilot.observability.redaction import REDACTED, redact


def test_valid_correlation_id_is_preserved() -> None:
    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.get("/health/live", headers={CORRELATION_HEADER: "caller-123"})

    assert response.headers[CORRELATION_HEADER] == "caller-123"


def test_invalid_correlation_id_is_replaced() -> None:
    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.get(
            "/health/live", headers={CORRELATION_HEADER: "unsafe value with spaces"}
        )

    replacement = response.headers[CORRELATION_HEADER]
    assert replacement.startswith("corr-")
    assert replacement != "unsafe value with spaces"


def test_redaction_recurses_through_sensitive_fields() -> None:
    data = {
        "authorization": "Bearer secret",
        "nested": {"api-key": "abc", "safe": "visible"},
        "items": [{"password": "guess-me"}],
    }

    assert redact(data) == {
        "authorization": REDACTED,
        "nested": {"api-key": REDACTED, "safe": "visible"},
        "items": [{"password": REDACTED}],
    }


def test_json_formatter_emits_machine_readable_redacted_event() -> None:
    record = logging.LogRecord(
        name="ops_pilot",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test.event",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "corr-test"
    record.access_token = "must-not-appear"

    result = json.loads(JsonFormatter().format(record))

    assert result["event"] == "test.event"
    assert result["correlation_id"] == "corr-test"
    assert result["access_token"] == REDACTED


def test_analysis_audit_event_joins_request_and_response() -> None:
    sink = InMemoryAuditSink()
    incident = {
        "schema_version": "1.0",
        "incident_id": "inc-audit-1",
        "occurred_at": "2026-09-20T12:00:00Z",
        "source": "synthetic-monitor",
        "severity": "medium",
        "signal_type": "unknown",
        "resource": "service:audit-demo",
        "summary": "Synthetic unknown incident",
        "evidence": [],
    }

    with TestClient(create_app(Settings(environment=Environment.TEST), audit_sink=sink)) as client:
        response = client.post(
            "/v1/incidents/analyze",
            json=incident,
            headers={CORRELATION_HEADER: "corr-audit-test"},
        )

    body = response.json()
    assert response.status_code == 200
    assert body["correlation_id"] == "corr-audit-test"
    assert sink.events[0].correlation_id == "corr-audit-test"
    assert sink.events[0].event_id == body["audit_event_id"]
