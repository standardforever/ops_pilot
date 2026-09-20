"""Versioned, strict domain models for incidents and triage output."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

SCHEMA_VERSION = "1.0"
Identifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2048)]


class DomainModel(BaseModel):
    """Strict immutable base for data crossing domain boundaries."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


class Severity(StrEnum):
    """Normalized incident severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(StrEnum):
    """Signals understood by the first analysis contract."""

    HIGH_CPU = "high_cpu"
    LOW_DISK_SPACE = "low_disk_space"
    FAILED_HEALTH_CHECK = "failed_health_check"
    UNKNOWN = "unknown"


class EvidenceKind(StrEnum):
    """Supported evidence representations."""

    METRIC = "metric"
    LOG = "log"
    EVENT = "event"
    OBSERVATION = "observation"


class RiskLevel(StrEnum):
    """Risk assigned to a proposed read-only action."""

    INFORMATIONAL = "informational"
    LOW = "low"


class ActionType(StrEnum):
    """Allow-listed investigation actions; none perform mutation."""

    INSPECT_METRICS = "inspect_metrics"
    INSPECT_DISK_USAGE = "inspect_disk_usage"
    INSPECT_HEALTH_STATE = "inspect_health_state"
    COLLECT_MORE_EVIDENCE = "collect_more_evidence"


class Evidence(DomainModel):
    """A structured fact considered during analysis."""

    evidence_id: Identifier = Field(description="Stable identifier referenced by analysis output")
    kind: EvidenceKind = Field(description="Evidence representation")
    name: ShortText = Field(description="Normalized evidence name")
    value: str | int | float | bool = Field(description="Synthetic observed value")
    unit: Annotated[str, StringConstraints(max_length=32)] | None = Field(
        default=None, description="Unit associated with a numeric value"
    )
    observed_at: AwareDatetime = Field(description="Timezone-aware observation timestamp")
    source: Identifier = Field(description="Synthetic evidence source")


class Incident(DomainModel):
    """Versioned incident accepted by the analysis API."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1.0",
                    "incident_id": "inc-demo-001",
                    "occurred_at": "2026-09-20T12:00:00Z",
                    "source": "synthetic-monitor",
                    "severity": "high",
                    "signal_type": "high_cpu",
                    "resource": "service:checkout-demo",
                    "summary": "Synthetic CPU saturation",
                    "evidence": [
                        {
                            "evidence_id": "ev-cpu-001",
                            "kind": "metric",
                            "name": "cpu_utilization_percent",
                            "value": 96.4,
                            "unit": "percent",
                            "observed_at": "2026-09-20T11:59:00Z",
                            "source": "synthetic-monitor",
                        }
                    ],
                }
            ]
        },
    )

    schema_version: Literal["1.0"] = Field(description="Incident contract version")
    incident_id: Identifier = Field(description="Caller-provided stable incident identifier")
    occurred_at: AwareDatetime = Field(description="Timezone-aware incident timestamp")
    source: Identifier = Field(description="Synthetic source system")
    severity: Severity = Field(description="Normalized incident severity")
    signal_type: SignalType = Field(description="Normalized signal analyzed by OpsPilot")
    resource: Identifier = Field(description="Synthetic affected resource identifier")
    summary: LongText = Field(description="Human-readable incident description")
    evidence: tuple[Evidence, ...] = Field(default=(), description="Structured input evidence")


class ActionProposal(DomainModel):
    """An investigation proposal; this model is never execution authorization."""

    action_id: Identifier = Field(description="Stable proposal identifier")
    action_type: ActionType = Field(description="Allow-listed read-only action type")
    title: ShortText = Field(description="Short action description")
    description: LongText = Field(description="Detailed operator instruction")
    read_only: Literal[True] = Field(description="Invariant prohibiting mutation")
    risk_level: RiskLevel = Field(description="Risk classification")
    requires_approval: bool = Field(description="Whether policy would require approval")


class Recommendation(DomainModel):
    """Evidence-linked investigation recommendation."""

    recommendation_id: Identifier
    summary: ShortText
    rationale: LongText
    evidence_ids: tuple[Identifier, ...] = Field(min_length=1)
    action: ActionProposal


class Hypothesis(DomainModel):
    """Possible cause with bounded confidence and supporting evidence."""

    hypothesis_id: Identifier
    summary: ShortText
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: tuple[Identifier, ...] = Field(min_length=1)


class TriagePlan(DomainModel):
    """Validated result of incident analysis."""

    schema_version: Literal["1.0"] = Field(description="Triage contract version")
    incident_id: Identifier
    correlation_id: Identifier
    audit_event_id: Identifier
    evidence_considered: tuple[Evidence, ...] = Field(min_length=1)
    hypotheses: tuple[Hypothesis, ...] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    recommendations: tuple[Recommendation, ...] = Field(min_length=1)
    limitations: tuple[ShortText, ...] = ()

    @model_validator(mode="after")
    def evidence_references_exist(self) -> Self:
        """Prevent analysis output from citing evidence it did not consider."""

        available = {item.evidence_id for item in self.evidence_considered}
        hypothesis_references = {
            evidence_id for item in self.hypotheses for evidence_id in item.evidence_ids
        }
        recommendation_references = {
            evidence_id for item in self.recommendations for evidence_id in item.evidence_ids
        }
        referenced = hypothesis_references | recommendation_references
        missing = referenced - available
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"analysis references unknown evidence: {missing_list}")
        return self


class AuditEvent(DomainModel):
    """Safe metadata describing a completed analysis decision."""

    schema_version: Literal["1.0"]
    event_id: Identifier
    event_name: Literal["analysis.completed"]
    occurred_at: AwareDatetime
    correlation_id: Identifier
    incident_id: Identifier
    signal_type: SignalType
    recommendation_count: int = Field(ge=0)
    outcome: Literal["completed"]


def utc_now() -> datetime:
    """Return an aware timestamp; isolated to simplify deterministic test injection later."""

    return datetime.now().astimezone()
