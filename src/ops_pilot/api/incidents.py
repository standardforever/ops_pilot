"""Incident analysis HTTP boundary."""

from uuid import uuid4

from fastapi import APIRouter

from ops_pilot.analysis import analyze_incident
from ops_pilot.api.errors import ErrorResponse
from ops_pilot.domain import Incident, TriagePlan

router = APIRouter(prefix="/v1/incidents", tags=["incidents"])


@router.post(
    "/analyze",
    response_model=TriagePlan,
    responses={422: {"model": ErrorResponse, "description": "Invalid incident contract"}},
    summary="Analyze a synthetic incident",
)
async def analyze(incident: Incident) -> TriagePlan:
    """Produce a deterministic read-only triage plan."""

    return analyze_incident(
        incident,
        correlation_id=f"corr-{uuid4().hex}",
        audit_event_id=f"audit-{uuid4().hex}",
    )
