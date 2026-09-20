# Week 1 Requirements and Safety Boundaries

| Field | Value |
|---|---|
| Status | Proposed |
| Scope | Local foundation and read-only incident analysis |
| Related issue | [#2](https://github.com/standardforever/ops_pilot/issues/2) |
| Parent epic | [#1](https://github.com/standardforever/ops_pilot/issues/1) |
| Last updated | 2026-09-20 |

## 1. Purpose

This document defines the product, engineering, and safety requirements for the first executable OpsPilot slice. It is the contract used by architecture, implementation, testing, continuous integration, security review, and demonstration work.

The objective is to prove that OpsPilot can accept a synthetic infrastructure incident and return an explainable, deterministic, read-only triage plan without connecting to or modifying real infrastructure.

## 2. Problem statement

Operations engineers often receive an alert before they have enough information to determine its cause. They must collect evidence, identify likely explanations, and decide which safe checks to perform next.

The first OpsPilot slice must demonstrate a controlled version of that workflow. It must validate an incident, analyze a small number of known conditions, return evidence-linked recommendations, and record enough information to audit the decision.

## 3. Primary user

The primary user is a developer or operations engineer running OpsPilot locally with synthetic incident data.

The user needs to:

- Confirm that the service is running and ready.
- Submit a versioned incident.
- Receive a structured triage plan.
- Understand which evidence produced each recommendation.
- Trace the request and resulting decision.
- Confirm that no infrastructure change was attempted.

## 4. Scope

### 4.1 In scope

- A locally runnable Python API
- Liveness and readiness endpoints
- A versioned incident request contract
- A versioned triage response contract
- Deterministic analysis for three synthetic incident types
- Safe fallback behavior for an unknown incident type
- Evidence-linked recommendations
- Correlation identifiers and structured audit events
- Docker and Docker Compose execution
- Automated formatting, linting, type checking, tests, and security checks
- GitHub Actions continuous integration

### 4.2 Out of scope

- Production infrastructure access
- AWS resources or credentials
- Kubernetes deployment
- Terraform or Ansible execution
- External AI or model-provider integration
- Automated remediation
- Arbitrary command or script execution
- Persistent database storage
- Authentication, authorization, or multi-tenancy
- A graphical user interface
- Production service-level objectives

Out-of-scope work requires a separate issue and must not be introduced implicitly through an implementation pull request.

## 5. Definitions

| Term | Definition |
|---|---|
| Incident | A versioned description of an observed infrastructure condition |
| Evidence | A structured fact used during analysis |
| Triage plan | An explanation, confidence level, and ordered set of recommended investigation steps |
| Action proposal | A structured description of a possible operation; it is not permission to execute |
| Correlation ID | An identifier connecting a request, logs, analysis, response, and audit event |
| Audit event | A structured record describing an important decision or state transition |
| Fail closed | Refuse or stop an operation when required information or policy is missing |

## 6. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| `FR-001` | The service shall expose `GET /health/live`. | API test returns HTTP 200 while the process is running. |
| `FR-002` | The service shall expose `GET /health/ready`. | API test returns HTTP 200 when required local components are initialized. |
| `FR-003` | The service shall expose `POST /v1/incidents/analyze`. | OpenAPI inspection and API test. |
| `FR-004` | The analysis endpoint shall accept only incidents that satisfy the versioned request schema. | Valid and invalid contract tests. |
| `FR-005` | The service shall analyze a synthetic high-CPU incident. | Fixture produces the documented high-CPU triage plan. |
| `FR-006` | The service shall analyze a synthetic low-disk-space incident. | Fixture produces the documented disk triage plan. |
| `FR-007` | The service shall analyze a synthetic failed-health-check incident. | Fixture produces the documented health-check triage plan. |
| `FR-008` | An unknown incident type shall produce a low-confidence investigation plan rather than a fabricated cause. | Unknown-signal API test. |
| `FR-009` | Every recommendation shall reference the evidence used to produce it. | Response-schema and analysis tests. |
| `FR-010` | Every action proposal shall declare whether it is read-only, its risk level, and whether approval would be required. | Domain-model validation tests. |
| `FR-011` | Every request shall accept a valid caller-provided correlation ID or generate one when absent. | Header and logging tests. |
| `FR-012` | The response shall include correlation and audit identifiers. | API response test. |
| `FR-013` | A completed analysis shall emit a structured audit event. | Captured-log or audit-sink test. |
| `FR-014` | Invalid input shall return a documented error contract and an appropriate 4xx status. | Parameterized invalid-input tests. |
| `FR-015` | Repeating the same valid incident shall produce semantically equivalent analysis output, excluding generated IDs and timestamps. | Determinism test. |

## 7. Non-functional requirements

| ID | Requirement | Verification |
|---|---|---|
| `NFR-001` | A contributor shall be able to bootstrap the project using documented commands from a clean clone. | Clean-environment walkthrough. |
| `NFR-002` | The application and tests shall run without cloud credentials or an external AI-provider key. | CI environment contains neither credential type. |
| `NFR-003` | Unit and API tests shall not require internet access. | Tests pass with external network access unavailable. |
| `NFR-004` | Runtime configuration shall use environment variables with safe local defaults. | Settings tests and configuration documentation. |
| `NFR-005` | Invalid required configuration shall fail during startup with a useful error that contains no secret value. | Startup-failure test. |
| `NFR-006` | Application logs shall be structured JSON outside the test environment. | Log-capture test. |
| `NFR-007` | The container shall run as a non-root user. | Container inspection and smoke test. |
| `NFR-008` | Local verification and CI shall execute the same underlying commands. | Review the task runner and workflow. |
| `NFR-009` | The initial codebase shall maintain at least 85% line coverage without excluding meaningful business logic. | CI coverage report. |
| `NFR-010` | Dependencies shall be locked or resolved reproducibly. | Clean installation produces the expected dependency set. |
| `NFR-011` | The service shall shut down cleanly when it receives a termination signal. | Container shutdown test. |
| `NFR-012` | Public API and domain models shall include descriptions and representative examples. | OpenAPI and schema review. |

## 8. Safety requirements

| ID | Requirement | Verification |
|---|---|---|
| `SAFE-001` | The system shall operate in read-only mode. | Architecture review and tests. |
| `SAFE-002` | The application shall not execute shell commands or scripts. | Code review and static search. |
| `SAFE-003` | The application shall not modify local or remote infrastructure. | Integration boundary review. |
| `SAFE-004` | The application shall not load AWS or other cloud credentials. | Configuration and environment tests. |
| `SAFE-005` | The application shall not call external AI or model-provider services. | Dependency and network-boundary review. |
| `SAFE-006` | Unsupported action types shall fail closed. | Domain validation tests. |
| `SAFE-007` | An action proposal shall never be treated as authorization to execute. | Component-boundary review. |
| `SAFE-008` | Secrets and configured sensitive fields shall be redacted from logs, errors, fixtures, and audit events. | Redaction tests. |
| `SAFE-009` | Validation failures shall not return stack traces or internal configuration values to the caller. | Error-response tests. |
| `SAFE-010` | Synthetic fixtures shall contain no real credentials, customer data, or production identifiers. | Fixture review and secret scan. |

## 9. Incident input contract

The detailed schema will be implemented as a versioned domain model. At minimum, an incident contains:

| Field | Requirement |
|---|---|
| `schema_version` | Required and supported by the API version |
| `incident_id` | Required stable identifier |
| `occurred_at` | Required timezone-aware timestamp |
| `source` | Required source-system identifier |
| `severity` | Required supported enumeration |
| `signal_type` | Required supported or explicitly unknown signal |
| `resource` | Required synthetic target identifier |
| `summary` | Required human-readable description |
| `evidence` | Optional structured input evidence |

## 10. Triage output contract

At minimum, a successful response contains:

| Field | Requirement |
|---|---|
| `schema_version` | Response-contract version |
| `incident_id` | Identifier copied from the request |
| `correlation_id` | Request-trace identifier |
| `audit_event_id` | Identifier of the completed-analysis audit event |
| `hypotheses` | Evidence-linked possible causes |
| `confidence` | Bounded confidence value with uncertainty preserved |
| `recommendations` | Ordered read-only investigation steps |
| `action_proposals` | Structured action metadata; never executable authorization |
| `limitations` | Missing evidence, unsupported conditions, or uncertainty |

## 11. Acceptance scenarios

### 11.1 Supported incident

**Given** a valid high-CPU synthetic incident  
**When** the user submits it for analysis  
**Then** the service returns a validated triage plan with evidence-linked recommendations, correlation and audit identifiers, and read-only action metadata.

### 11.2 Unknown incident

**Given** a valid incident with an unsupported signal type  
**When** the user submits it for analysis  
**Then** the service returns a low-confidence investigation plan, states its limitations, and does not invent a definitive cause.

### 11.3 Invalid incident

**Given** an incident missing a required field  
**When** the user submits it for analysis  
**Then** the service returns the documented validation-error contract and does not begin analysis.

### 11.4 Attempted unsafe action

**Given** an analysis rule or input that refers to an unsupported mutating action  
**When** the action proposal is validated  
**Then** validation fails closed and an auditable error is produced.

## 12. Assumptions and constraints

- All incident and evidence data is synthetic.
- One local process is sufficient; horizontal scaling is not required.
- In-memory workflow state is acceptable for the first slice.
- The deterministic analysis rules are part of the application process.
- Authentication and authorization are deferred because the service is local-only and non-mutating.
- Python 3.12 or later and Docker are expected development prerequisites.
- Security boundaries defined here must remain valid when later integrations are introduced.

## 13. Unresolved questions

| Question | Owner | Resolution point |
|---|---|---|
| Which Python dependency-management tool will be used? | Architecture owner | ADR and service scaffold |
| Should audit events initially use standard output, an in-memory sink, or a local file? | Architecture owner | Logging/audit design |
| Which exact confidence representation will the contract use? | Domain-model owner | Domain contract implementation |
| Which header name and validation rules will be used for correlation IDs? | API owner | API scaffold |
| Should readiness include only application initialization or also an audit-sink check? | API owner | Health endpoint design |

An unresolved question blocks implementation only when the affected issue cannot satisfy its acceptance criteria without the decision.

## 14. Requirements traceability

| Requirement group | Implementation issue | Primary evidence |
|---|---|---|
| `FR-001`–`FR-003`, `FR-014`, `NFR-004`, `NFR-005` | [#5](https://github.com/standardforever/ops_pilot/issues/5) | Health/API/configuration tests |
| `FR-004`, `FR-009`, `FR-010`, `NFR-012`, `SAFE-006`, `SAFE-007` | [#6](https://github.com/standardforever/ops_pilot/issues/6) | Contract and domain-model tests |
| `FR-005`–`FR-008`, `FR-015`, `SAFE-001`–`SAFE-005` | [#7](https://github.com/standardforever/ops_pilot/issues/7) | Analysis-engine tests |
| `FR-011`–`FR-013`, `NFR-006`, `SAFE-008`, `SAFE-009` | [#8](https://github.com/standardforever/ops_pilot/issues/8) | Logging, audit, and redaction tests |
| `NFR-001`, `NFR-007`, `NFR-010`, `NFR-011` | [#9](https://github.com/standardforever/ops_pilot/issues/9) | Container and clean-start tests |
| `NFR-003`, `NFR-009` | [#10](https://github.com/standardforever/ops_pilot/issues/10) | Test and coverage reports |
| `NFR-002`, `NFR-008` | [#11](https://github.com/standardforever/ops_pilot/issues/11) | GitHub Actions run |
| Safety baseline and `SAFE-010` | [#12](https://github.com/standardforever/ops_pilot/issues/12) | Security scans and threat model |
| Clean-clone acceptance scenarios | [#13](https://github.com/standardforever/ops_pilot/issues/13) | Reproducible demonstration |

## 15. Approval criteria

This requirements document is ready for implementation when:

- Every requirement has a stable identifier.
- Every requirement has a verification method.
- Scope and non-goals are unambiguous.
- Safety requirements prohibit execution and real infrastructure access.
- Architecture documents are consistent with these requirements.
- Unresolved questions have an owner and a resolution point.
- The traceability table covers every requirement group.
