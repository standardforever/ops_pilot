"""Incident analysis HTTP boundary."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Request

from ops_pilot.analysis import analyze_incident
from ops_pilot.api.errors import ErrorResponse
from ops_pilot.domain import AuditEvent, Incident, TriagePlan

router = APIRouter(prefix="/v1/incidents", tags=["incidents"])


@router.post(
    "/analyze",
    response_model=TriagePlan,
    responses={422: {"model": ErrorResponse, "description": "Invalid incident contract"}},
    summary="Analyze a synthetic incident",
)
async def analyze(incident: Incident, request: Request) -> TriagePlan:
    """Produce a deterministic read-only triage plan."""

    correlation_id: str = request.state.correlation_id
    audit_event_id = f"audit-{uuid4().hex}"
    plan = analyze_incident(
        incident,
        correlation_id=correlation_id,
        audit_event_id=audit_event_id,
    )
    event = AuditEvent(
        schema_version="1.0",
        event_id=audit_event_id,
        event_name="analysis.completed",
        occurred_at=datetime.now(tz=UTC),
        correlation_id=correlation_id,
        incident_id=incident.incident_id,
        signal_type=incident.signal_type,
        recommendation_count=len(plan.recommendations),
        outcome="completed",
    )
    request.app.state.audit_sink.emit(event)
    return plan
