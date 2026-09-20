"""Pure, deterministic rules for the read-only Week 1 analysis slice."""

from dataclasses import dataclass

from ops_pilot.domain import (
    ActionProposal,
    ActionType,
    Evidence,
    EvidenceKind,
    Hypothesis,
    Incident,
    Recommendation,
    RiskLevel,
    SignalType,
    TriagePlan,
)


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Internal immutable output from a selected rule."""

    hypothesis: str
    confidence: float
    recommendation: str
    rationale: str
    action_type: ActionType
    action_title: str
    action_description: str
    limitations: tuple[str, ...]


RULES: dict[SignalType, RuleResult] = {
    SignalType.HIGH_CPU: RuleResult(
        hypothesis="Sustained workload or a busy process may be saturating CPU capacity.",
        confidence=0.85,
        recommendation="Compare CPU utilization with workload and process-level evidence.",
        rationale=(
            "The synthetic incident reports CPU saturation; read-only metrics can distinguish "
            "transient load from sustained pressure."
        ),
        action_type=ActionType.INSPECT_METRICS,
        action_title="Inspect CPU metrics",
        action_description=(
            "Review synthetic CPU, load, and request-rate metrics for the affected resource "
            "and time window."
        ),
        limitations=(
            "No process profile, deployment history, or live infrastructure data was queried.",
        ),
    ),
    SignalType.LOW_DISK_SPACE: RuleResult(
        hypothesis="Accumulated data may be consuming the available filesystem capacity.",
        confidence=0.88,
        recommendation="Inspect filesystem utilization and identify the largest synthetic paths.",
        rationale=(
            "Low free-space evidence is consistent with growth in logs, caches, artifacts, "
            "or application data."
        ),
        action_type=ActionType.INSPECT_DISK_USAGE,
        action_title="Inspect disk usage",
        action_description=(
            "Review synthetic filesystem capacity and path-level usage without deleting or "
            "modifying data."
        ),
        limitations=("No filesystem was mounted and no cleanup action was attempted.",),
    ),
    SignalType.FAILED_HEALTH_CHECK: RuleResult(
        hypothesis=(
            "The service may be unavailable, still initializing, or unable to satisfy a local "
            "dependency check."
        ),
        confidence=0.8,
        recommendation="Inspect synthetic health state and recent application events.",
        rationale=(
            "A failed health signal identifies availability loss but does not by itself identify "
            "the failing component."
        ),
        action_type=ActionType.INSPECT_HEALTH_STATE,
        action_title="Inspect health state",
        action_description=(
            "Review synthetic readiness state and sanitized application events for the "
            "affected resource."
        ),
        limitations=("No live endpoint, orchestrator, or dependency was contacted.",),
    ),
    SignalType.UNKNOWN: RuleResult(
        hypothesis="The available signal is insufficient to identify a likely cause.",
        confidence=0.2,
        recommendation=(
            "Collect additional read-only evidence before forming a stronger hypothesis."
        ),
        rationale=(
            "OpsPilot does not have a deterministic rule for this signal and will not invent a "
            "definitive cause."
        ),
        action_type=ActionType.COLLECT_MORE_EVIDENCE,
        action_title="Collect more evidence",
        action_description=(
            "Gather synthetic metrics, events, and health observations relevant to the "
            "incident window."
        ),
        limitations=(
            "The signal is explicitly unknown.",
            "No definitive cause can be inferred from the available evidence.",
        ),
    ),
}


def _evidence_for(incident: Incident) -> tuple[Evidence, ...]:
    """Use caller evidence or derive one safe observation from the validated request."""

    if incident.evidence:
        return incident.evidence
    return (
        Evidence(
            evidence_id="ev-incident-signal",
            kind=EvidenceKind.OBSERVATION,
            name="reported_signal_type",
            value=incident.signal_type.value,
            observed_at=incident.occurred_at,
            source=incident.source,
        ),
    )


def analyze_incident(
    incident: Incident,
    *,
    correlation_id: str,
    audit_event_id: str,
) -> TriagePlan:
    """Return a deterministic plan without performing I/O or executing actions."""

    rule = RULES[incident.signal_type]
    evidence = _evidence_for(incident)
    evidence_ids = tuple(item.evidence_id for item in evidence)
    signal_slug = incident.signal_type.value.replace("_", "-")
    action = ActionProposal(
        action_id=f"action-{signal_slug}",
        action_type=rule.action_type,
        title=rule.action_title,
        description=rule.action_description,
        read_only=True,
        risk_level=RiskLevel.INFORMATIONAL,
        requires_approval=False,
    )
    return TriagePlan(
        schema_version="1.0",
        incident_id=incident.incident_id,
        correlation_id=correlation_id,
        audit_event_id=audit_event_id,
        evidence_considered=evidence,
        hypotheses=(
            Hypothesis(
                hypothesis_id=f"hypothesis-{signal_slug}",
                summary=rule.hypothesis,
                confidence=rule.confidence,
                evidence_ids=evidence_ids,
            ),
        ),
        confidence=rule.confidence,
        recommendations=(
            Recommendation(
                recommendation_id=f"recommendation-{signal_slug}",
                summary=rule.recommendation,
                rationale=rule.rationale,
                evidence_ids=evidence_ids,
                action=action,
            ),
        ),
        limitations=rule.limitations,
    )
