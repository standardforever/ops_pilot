"""Deterministic incident analysis behavior."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ops_pilot.analysis import analyze_incident
from ops_pilot.application import create_app
from ops_pilot.config import Environment, Settings
from ops_pilot.domain import Incident, SignalType

FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures" / "incidents"


def load_incident(name: str) -> Incident:
    data: dict[str, Any] = json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))
    return Incident.model_validate(data)


@pytest.mark.parametrize(
    ("fixture_name", "signal_type"),
    [
        ("high_cpu.json", SignalType.HIGH_CPU),
        ("low_disk_space.json", SignalType.LOW_DISK_SPACE),
        ("failed_health_check.json", SignalType.FAILED_HEALTH_CHECK),
    ],
)
def test_supported_scenario_returns_evidence_linked_read_only_plan(
    fixture_name: str, signal_type: SignalType
) -> None:
    incident = load_incident(fixture_name)

    plan = analyze_incident(incident, correlation_id="corr-test", audit_event_id="audit-test")

    assert incident.signal_type is signal_type
    assert plan.confidence >= 0.8
    assert plan.recommendations[0].evidence_ids
    assert plan.recommendations[0].action.read_only is True


def test_analysis_is_semantically_deterministic() -> None:
    incident = load_incident("high_cpu.json")

    first = analyze_incident(incident, correlation_id="corr-1", audit_event_id="audit-1")
    second = analyze_incident(incident, correlation_id="corr-2", audit_event_id="audit-2")

    first_data = first.model_dump(exclude={"correlation_id", "audit_event_id"})
    second_data = second.model_dump(exclude={"correlation_id", "audit_event_id"})
    assert first_data == second_data


def test_unknown_signal_preserves_uncertainty_and_adds_safe_evidence() -> None:
    plan = analyze_incident(
        load_incident("unknown.json"),
        correlation_id="corr-test",
        audit_event_id="audit-test",
    )

    assert plan.confidence <= 0.2
    assert "unknown" in " ".join(plan.limitations).lower()
    assert plan.evidence_considered[0].name == "reported_signal_type"
    assert plan.recommendations[0].action.read_only is True


def test_api_returns_validated_triage_plan() -> None:
    incident_data = json.loads((FIXTURE_DIRECTORY / "high_cpu.json").read_text(encoding="utf-8"))

    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.post("/v1/incidents/analyze", json=incident_data)

    assert response.status_code == 200
    body = response.json()
    assert body["incident_id"] == "inc-demo-001"
    assert body["recommendations"][0]["action"]["read_only"] is True


def test_api_returns_safe_documented_validation_error() -> None:
    invalid = json.loads(
        (FIXTURE_DIRECTORY / "invalid_missing_incident_id.json").read_text(encoding="utf-8")
    )

    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.post("/v1/incidents/analyze", json=invalid)

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "invalid_request"
    assert "traceback" not in response.text.lower()
    assert "input" not in body
