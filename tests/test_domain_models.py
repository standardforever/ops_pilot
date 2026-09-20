"""Contract and invariant tests for framework-independent domain models."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ops_pilot.domain import (
    ActionProposal,
    ActionType,
    Evidence,
    EvidenceKind,
    Hypothesis,
    Incident,
    Recommendation,
    RiskLevel,
    TriagePlan,
)

FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures" / "incidents"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))


def test_valid_incident_fixture_satisfies_contract() -> None:
    incident = Incident.model_validate(load_fixture("high_cpu.json"))

    assert incident.incident_id == "inc-demo-001"
    assert incident.evidence[0].evidence_id == "ev-cpu-001"


def test_invalid_fixture_rejects_required_enum_and_timestamp_errors() -> None:
    with pytest.raises(ValidationError) as error:
        Incident.model_validate(load_fixture("invalid_missing_incident_id.json"))

    locations = {tuple(item["loc"]) for item in error.value.errors()}
    assert {("incident_id",), ("occurred_at",), ("severity",)} <= locations


def test_mutating_action_is_impossible_to_construct() -> None:
    with pytest.raises(ValidationError):
        ActionProposal.model_validate(
            {
                "action_id": "action-1",
                "action_type": "inspect_metrics",
                "title": "Inspect metrics",
                "description": "Read synthetic metrics.",
                "read_only": False,
                "risk_level": "low",
                "requires_approval": False,
            }
        )


def test_unsupported_action_type_fails_closed() -> None:
    with pytest.raises(ValidationError):
        ActionProposal.model_validate(
            {
                "action_id": "action-1",
                "action_type": "restart_service",
                "title": "Restart service",
                "description": "This action is not allowed.",
                "read_only": True,
                "risk_level": "low",
                "requires_approval": True,
            }
        )


def test_triage_plan_rejects_unknown_evidence_reference() -> None:
    evidence = Evidence(
        evidence_id="ev-known",
        kind=EvidenceKind.OBSERVATION,
        name="synthetic_observation",
        value="present",
        observed_at=datetime(2026, 9, 20, tzinfo=UTC),
        source="test",
    )
    action = ActionProposal(
        action_id="action-1",
        action_type=ActionType.COLLECT_MORE_EVIDENCE,
        title="Collect evidence",
        description="Collect more synthetic evidence without changing the resource.",
        read_only=True,
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
    )

    with pytest.raises(ValidationError, match="unknown evidence"):
        TriagePlan(
            schema_version="1.0",
            incident_id="inc-1",
            correlation_id="corr-1",
            audit_event_id="audit-1",
            evidence_considered=(evidence,),
            hypotheses=(
                Hypothesis(
                    hypothesis_id="hyp-1",
                    summary="Insufficient evidence",
                    confidence=0.1,
                    evidence_ids=("ev-missing",),
                ),
            ),
            confidence=0.1,
            recommendations=(
                Recommendation(
                    recommendation_id="rec-1",
                    summary="Collect more evidence",
                    rationale="The signal is not recognized.",
                    evidence_ids=("ev-known",),
                    action=action,
                ),
            ),
        )


def test_domain_module_has_no_fastapi_dependency() -> None:
    source = (Path(__file__).parents[1] / "src" / "ops_pilot" / "domain" / "models.py").read_text(
        encoding="utf-8"
    )
    assert "fastapi" not in source.lower()
