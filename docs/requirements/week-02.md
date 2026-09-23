# Week 2 Requirements and Safety Boundaries

| Field | Value |
|---|---|
| Status | Proposed |
| Scope | Local, read-only Linux evidence collection and deterministic analysis reuse |
| Related issue | [#31](https://github.com/standardforever/ops_pilot/issues/31) |
| Parent epic | [#30](https://github.com/standardforever/ops_pilot/issues/30) |
| Builds on | [Week 1 requirements](week-01.md) |
| Last updated | 2026-09-23 |

## 1. Purpose

This document defines the product, engineering, safety, privacy, and verification requirements for OpsPilot's first real evidence-collection capability. It is the contract used by the Week 2 architecture, domain models, collectors, API, deterministic analysis, audit behavior, tests, continuous integration, and demonstration.

The objective is to prove that OpsPilot can collect a bounded set of Linux runtime measurements, return them as versioned and provenance-linked evidence, and reuse that evidence during deterministic incident analysis without creating an infrastructure-execution path.

The Week 1 requirements remain in force unless this document introduces a stricter rule. Week 2 does not relax the read-only, fail-closed, redaction, audit, or separation-of-duties boundaries established in Week 1.

## 2. Problem statement

Week 1 analysis accepts structured evidence supplied with a synthetic incident. It does not obtain evidence from an operating environment. An operator must therefore construct every observation before OpsPilot can analyze it.

OpsPilot needs a controlled collection boundary that can obtain useful operational facts while preserving the difference between observing a system and controlling it. A collector failure must be visible, an observation must identify its source, and missing data must never be replaced with a plausible-looking value.

The Week 2 slice must demonstrate that boundary locally before cloud, Kubernetes, remote-host, or privileged integrations are introduced.

## 3. Primary user and user journey

The primary user is a developer or operations engineer running OpsPilot on Linux or in the documented Linux container runtime.

The user needs to:

1. Confirm that the service and configured collector registry are ready.
2. Request one or more approved collectors for a supported Linux target.
3. Receive load, memory, and disk observations with units, timestamps, sources, and provenance.
4. Distinguish successful, unavailable, failed, and timed-out collectors.
5. Understand whether the overall snapshot succeeded, partially succeeded, or failed.
6. Trace the request, collector outcomes, response, and audit event with one correlation ID.
7. Reuse successful evidence objects in the existing incident-analysis request without changing their fields.
8. Confirm that no command, mutation, credential access, external network call, or privilege escalation occurred.

## 4. Scope and non-goals

### 4.1 In scope

- A versioned `POST /v1/evidence/collect` endpoint
- A single supported target type: `linux_host`
- A static registry of known collector implementations
- Operator-controlled enablement of registered collectors
- Per-collector timeouts
- Linux load evidence from `/proc/loadavg` and the Python CPU-count API
- Linux memory evidence from `/proc/meminfo`
- Disk-usage evidence from Python standard-library filesystem statistics for configured paths
- Evidence and provenance contracts
- Successful, partial, and failed snapshots
- Structured collection logs and typed audit events
- Reuse of collected `Evidence` objects by `POST /v1/incidents/analyze`
- Deterministic high-load and disk-pressure interpretation
- Unit, contract, API, integration, container, smoke, and security verification
- A reproducible local runbook and Week 2 demonstration

### 4.2 Non-goals

- AWS resources, SDKs, APIs, or credentials
- Terraform or Ansible execution
- Kubernetes, Helm, Prometheus, Grafana, or Argo CD
- SSH or remote-host collection
- Docker Engine API or Docker socket access
- Process management, service management, or command execution
- Automatic remediation or infrastructure mutation
- Persistent evidence storage or historical querying
- Arbitrary file, directory, environment, or socket inspection
- External AI or model-provider integration
- A new memory-pressure incident type
- Authentication, authorization, multi-tenancy, or a graphical interface
- A claim that container measurements describe the physical host

Out-of-scope behavior requires a separate issue and requirements review. It must not enter Week 2 through a collector implementation, configuration option, or convenience endpoint.

## 5. Definitions

| Term | Definition |
|---|---|
| Collector | A statically registered component that obtains one bounded category of read-only evidence |
| Collector registry | The application-owned mapping of approved collector names to implementations |
| Enabled collector | A registered collector the operator has allowed through validated startup configuration |
| Collection request | A versioned request naming a supported target and one to three enabled collectors |
| Collection result | The outcome, evidence, provenance, timing, and safe errors for one collector |
| Evidence snapshot | The aggregate response for one collection request |
| Evidence provenance | Metadata linking an evidence ID to its collector version and normalized source reference |
| Approved source | A source explicitly listed in Section 9 and accessed only through the specified read-only mechanism |
| Unavailable | An expected condition in which an approved source cannot be observed and no evidence is returned |
| Failed | A collector encountered a safe, mapped failure and returned no fabricated evidence |
| Timed out | A collector did not finish inside its configured independent deadline |
| Partial snapshot | At least one requested collector succeeded and at least one did not succeed |
| Runtime scope | The Linux namespace and filesystem view visible to the OpsPilot process, normally its container |
| Source reference | A normalized identifier such as `procfs:loadavg`, never a machine-specific path |
| Fail closed | Refuse or stop behavior when registration, enablement, validation, provenance, audit, or safety requirements are not satisfied |

## 6. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| `COL-FR-001` | The service shall expose `POST /v1/evidence/collect`. | OpenAPI inspection and API test. |
| `COL-FR-002` | The endpoint shall accept only the versioned request fields defined in Section 10. | Valid, missing-field, extra-field, and unsupported-version API tests. |
| `COL-FR-003` | Week 2 shall support only `target_type=linux_host`. | Contract test rejects every other target type. |
| `COL-FR-004` | A request shall execute only collectors that are both statically registered and enabled by validated startup configuration. | Registry and API tests for registered, unknown, enabled, and disabled names. |
| `COL-FR-005` | A request shall contain one to three unique collector names, and result order shall match request order. | Boundary, duplicate, maximum-size, and ordering tests. |
| `COL-FR-006` | `linux.load` shall return the load and CPU-count evidence listed in Section 9. | Fixture-backed collector tests verify names, values, and units. |
| `COL-FR-007` | `linux.memory` shall return the memory evidence and calculations listed in Section 9. | Fixture-backed collector tests verify names, calculations, and units. |
| `COL-FR-008` | `linux.disk` shall return disk evidence for configured paths using the names and calculations in Section 9. | Injected-stat collector tests verify configured paths, calculations, and units. |
| `COL-FR-009` | Every returned evidence item shall contain an ID, kind, name, value, unit, timezone-aware observation time, and collector source. | Domain and API response tests. |
| `COL-FR-010` | Every evidence item shall have exactly one matching provenance record containing its evidence ID, collector name and version, source type, normalized source reference, and `read_only=true`. | Domain invariant and serialization tests. |
| `COL-FR-011` | The collection service shall enforce an independent configured timeout for each collector. | Fake-collector timeout tests. |
| `COL-FR-012` | Each requested collector shall produce exactly one ordered result with status `succeeded`, `unavailable`, `failed`, or `timed_out`. | Orchestration tests for every result state. |
| `COL-FR-013` | The aggregate status shall be `succeeded` when every result succeeds, `partial` when some but not all succeed, and `failed` when none succeed. | Domain and orchestration aggregation tests. |
| `COL-FR-014` | A non-successful collector shall return no fabricated evidence and at least one stable, safe error. | Failure, unavailable-source, malformed-source, and timeout tests. |
| `COL-FR-015` | The API shall preserve a valid caller correlation ID or generate a safe replacement and return the same ID in the header, snapshot, logs, and audit event. | Middleware, API, log, and audit tests. |
| `COL-FR-016` | Every collection attempt that reaches orchestration shall emit one typed `evidence.collection.completed` audit event. | Captured audit-sink tests for success, partial, and failure. |
| `COL-FR-017` | Invalid requests shall use the existing versioned `ErrorResponse` and shall not begin collection. | Parameterized API tests and fake-collector call assertions. |
| `COL-FR-018` | Evidence returned in `results[].evidence` shall use the existing `Evidence` contract and be reusable unchanged in `Incident.evidence`. | Contract compatibility and collect-then-analyze integration tests. |
| `COL-FR-019` | High-CPU analysis shall interpret `system_load_1m_per_cpu` using the thresholds in Section 10 without describing load average as CPU utilization. | Analyzer boundary tests at 0.70 and 1.00. |
| `COL-FR-020` | Low-disk analysis shall interpret `disk_used_percent` using the thresholds in Section 10 and use `disk_free_bytes` as supporting evidence when present. | Analyzer boundary tests at 80 and 90 percent. |
| `COL-FR-021` | Missing, unavailable, future, or stale relevant evidence shall reduce certainty and add a limitation rather than produce a definitive cause. | Analyzer tests for each evidence-quality condition. |
| `COL-FR-022` | Collection readiness shall fail when enabled collector configuration cannot be resolved to a valid registry. | Settings/startup and readiness tests. |
| `COL-FR-023` | The API shall document successful, partial, failed, and invalid examples in OpenAPI. | Generated OpenAPI schema review and tests. |
| `COL-FR-024` | Repeating collection with identical injected source data, clock, and ID providers shall produce semantically identical output. | Determinism unit test. |
| `COL-FR-025` | The executable demonstration shall cover health, success, partial failure, rejection, analysis reuse, correlation, audit, and read-only invariants. | Clean-clone Week 2 demonstration. |

## 7. Non-functional requirements

| ID | Requirement | Verification |
|---|---|---|
| `COL-NFR-001` | Collector, contract, API, and analysis tests shall run without internet access. | CI test environment and dependency review. |
| `COL-NFR-002` | Tests shall not depend on the executing machine's current load, memory, or disk values. | Review fixtures and injected reader/stat providers. |
| `COL-NFR-003` | Collector I/O, clocks, and ID generation shall be replaceable in tests. | Unit tests use fakes without patching global runtime state. |
| `COL-NFR-004` | `OPSPILOT_ENABLED_COLLECTORS` shall default to `linux.load,linux.memory,linux.disk` and reject unknown names during startup. | Configuration tests. |
| `COL-NFR-005` | `OPSPILOT_COLLECTOR_TIMEOUT_SECONDS` shall default to `2.0` and accept values from `0.1` through `30.0` seconds inclusive. | Configuration boundary tests. |
| `COL-NFR-006` | `OPSPILOT_DISK_PATHS` shall default to `/` and accept only normalized, unique, absolute operator-configured paths. | Configuration tests for valid, duplicate, relative, and malformed paths. |
| `COL-NFR-007` | One collector failure or timeout shall not discard successful results from other requested collectors. | Partial-result orchestration tests. |
| `COL-NFR-008` | Collection state shall not leak or mutate across concurrent requests. | Concurrency/isolation test. |
| `COL-NFR-009` | All public collection models shall be strict, immutable, documented, and reject unknown fields. | Pydantic contract and schema tests. |
| `COL-NFR-010` | All timestamps shall be timezone-aware ISO 8601 values; durations shall be non-negative integer milliseconds. | Domain boundary tests. |
| `COL-NFR-011` | Collection logs shall remain structured JSON outside tests. | Log-capture test. |
| `COL-NFR-012` | Local verification and CI shall use the same underlying `make verify` quality gate. | Makefile/workflow review. |
| `COL-NFR-013` | Branch-aware test coverage shall remain at or above the configured 85 percent threshold without excluding failure logic. | CI coverage report. |
| `COL-NFR-014` | The container shall remain non-root, use a read-only root filesystem, drop capabilities, and require no privileged mode. | Compose/image inspection and runtime smoke test. |
| `COL-NFR-015` | Dependency installation shall remain reproducible through the repository lockfile. | Clean installation and lockfile review. |
| `COL-NFR-016` | A contributor shall be able to reproduce the Week 2 demo from a clean clone using documented commands. | Independent runbook walkthrough. |
| `COL-NFR-017` | Unexpected internal errors shall produce a stable safe response and preserve a diagnostic correlation ID. | Fault-injection API test. |

## 8. Safety and privacy requirements

| ID | Requirement | Verification |
|---|---|---|
| `COL-SAFE-001` | Collection shall be read-only and shall not mutate files, processes, services, containers, or infrastructure. | Architecture review, code review, and smoke verification. |
| `COL-SAFE-002` | Collector code shall not execute shell commands, scripts, subprocesses, or external binaries. | AST/static security check and code review. |
| `COL-SAFE-003` | The API shall not accept caller-controlled file paths, commands, URLs, environment names, module names, callables, or arbitrary collector parameters. | Contract and adversarial API tests. |
| `COL-SAFE-004` | Collector implementations shall be statically registered; runtime module discovery, entry-point discovery, and dynamic imports are prohibited. | Registry review and targeted static test. |
| `COL-SAFE-005` | OpsPilot shall not mount, connect to, or instruct users to expose the Docker socket. | Compose, documentation, and repository scan. |
| `COL-SAFE-006` | Collection shall not require `sudo`, privileged mode, additional Linux capabilities, device mounts, or a writable root filesystem. | Container configuration and runtime inspection. |
| `COL-SAFE-007` | The application shall not load AWS, Kubernetes, Terraform, Ansible, SSH, AI-provider, or other infrastructure credentials. | Configuration/dependency review and secret scan. |
| `COL-SAFE-008` | Collectors and tests shall not make external network calls. | Dependency review and offline verification. |
| `COL-SAFE-009` | Collectors shall read only the approved sources and mechanisms in Section 9. | Collector tests, architecture review, and source inspection. |
| `COL-SAFE-010` | Missing, malformed, inaccessible, inconsistent, or non-finite source data shall never be replaced with zero, a default measurement, or an inferred value. | Negative-path collector tests. |
| `COL-SAFE-011` | API responses, errors, logs, audit events, fixtures, and documentation shall not expose raw procfs content, environment mappings, credentials, stack traces, or machine-specific paths. | Redaction, snapshot, error, and documentation tests/review. |
| `COL-SAFE-012` | Logs shall omit evidence values by default and record only the safe metadata allow-list in Section 10. | Structured log tests. |
| `COL-SAFE-013` | Likely sensitive keys and nested values shall pass through the central redaction policy before logging. | Parameterized recursive-redaction tests. |
| `COL-SAFE-014` | Source paths shall be represented externally only by normalized source references defined in Section 9. | Contract and API snapshot tests. |
| `COL-SAFE-015` | Unknown, disabled, duplicated, or unsupported collector requests shall fail before any collector runs. | Fake-collector non-invocation tests. |
| `COL-SAFE-016` | A required audit-sink failure shall prevent the collection from being reported as successful. | Audit fault-injection test. |
| `COL-SAFE-017` | Evidence snapshots shall remain request-scoped and in memory; Week 2 shall not add durable evidence storage. | Architecture and dependency review. |
| `COL-SAFE-018` | Reusing evidence in analysis shall not authorize or execute any action proposal. | Domain invariant and end-to-end review. |

## 9. Approved evidence sources

### 9.1 Source allow-list

| Collector | Approved mechanism | Normalized source reference | Evidence name | Value and unit |
|---|---|---|---|---|
| `linux.load` | Read `/proc/loadavg` | `procfs:loadavg` | `system_load_1m` | Non-negative finite float, `load` |
| `linux.load` | Read `/proc/loadavg` | `procfs:loadavg` | `system_load_5m` | Non-negative finite float, `load` |
| `linux.load` | Read `/proc/loadavg` | `procfs:loadavg` | `system_load_15m` | Non-negative finite float, `load` |
| `linux.load` | Python CPU-count API | `runtime:cpu_count` | `logical_cpu_count` | Positive integer, `count` |
| `linux.load` | Derived from approved load and CPU-count values | `derived:load_per_cpu` | `system_load_1m_per_cpu` | Non-negative finite float, `ratio` |
| `linux.memory` | Read required keys from `/proc/meminfo` | `procfs:meminfo` | `memory_total_bytes` | Positive integer, `bytes` |
| `linux.memory` | Read required keys from `/proc/meminfo` | `procfs:meminfo` | `memory_available_bytes` | Integer from 0 through total, `bytes` |
| `linux.memory` | `total - available` | `derived:memory_used` | `memory_used_bytes` | Integer from 0 through total, `bytes` |
| `linux.memory` | `used / total * 100` | `derived:memory_used_percent` | `memory_used_percent` | Float from 0 through 100, `percent` |
| `linux.disk` | Python `shutil.disk_usage` or equivalent standard-library stat for configured paths | `filesystem:<configured-id>` | `disk_total_bytes` | Positive integer, `bytes` |
| `linux.disk` | Same approved stat | `filesystem:<configured-id>` | `disk_used_bytes` | Non-negative integer, `bytes` |
| `linux.disk` | Same approved stat | `filesystem:<configured-id>` | `disk_free_bytes` | Non-negative integer, `bytes` |
| `linux.disk` | `used / total * 100` | `derived:disk_used_percent:<configured-id>` | `disk_used_percent` | Float from 0 through 100, `percent` |

The default configured disk path `/` uses the external resource and source identifier `filesystem:root`. Additional paths require operator configuration, validation, documentation, and a stable non-sensitive identifier. API callers cannot add or override paths.

### 9.2 Observation scope

Evidence describes the runtime scope visible to the OpsPilot process. Under Docker Compose this normally means the container's procfs, CPU view, memory view, and mounted filesystem view. Week 2 must not describe these values as measurements of the physical host unless a later, separately approved architecture explicitly establishes that boundary.

Every snapshot shall include this limitation when running in a container or when the scope cannot be proven:

> Measurements describe the OpsPilot runtime namespace, not an unconfigured physical host.

### 9.3 Prohibited sources and mechanisms

The following are not approved:

- Arbitrary `/proc`, `/sys`, `/dev`, or filesystem paths
- Process command lines or process environments
- General environment-variable enumeration
- Credential, key, token, or secret files
- Docker, containerd, CRI, SSH, cloud, or Kubernetes sockets/APIs
- Network endpoints
- Package metadata or dynamic plugin entry points
- Commands such as `top`, `free`, `df`, `ps`, `cat`, or shell pipelines

## 10. Collection request and response behavior

### 10.1 Request

`POST /v1/evidence/collect` accepts `application/json` only.

| Field | Type | Required | Rules |
|---|---|---|---|
| `schema_version` | String | Yes | Exactly `1.0` |
| `target.target_id` | Identifier string | Yes | Existing identifier constraints; describes the caller's logical target |
| `target.target_type` | String | Yes | Exactly `linux_host` |
| `collectors` | Array of strings | Yes | One to three unique, registered, enabled collector names |

Example:

```json
{
  "schema_version": "1.0",
  "target": {
    "target_id": "local-runtime",
    "target_type": "linux_host"
  },
  "collectors": [
    "linux.load",
    "linux.memory",
    "linux.disk"
  ]
}
```

No other request field is permitted.

### 10.2 Successful, partial, and failed snapshot

| Field | Type | Requirement |
|---|---|---|
| `schema_version` | String | Exactly `1.0` |
| `collection_id` | Identifier string | Server-generated unique collection identifier |
| `correlation_id` | Identifier string | Matches the response header and audit/log context |
| `target` | Object | Validated `target_id` and `target_type` copied from the request |
| `status` | String | `succeeded`, `partial`, or `failed` according to `COL-FR-013` |
| `started_at` | Timestamp | Timezone-aware start time |
| `completed_at` | Timestamp | Timezone-aware completion time not before `started_at` |
| `results` | Array | Exactly one result per requested collector, in request order |
| `audit_event_id` | Identifier string | ID of the required collection completion audit event |
| `limitations` | Array of strings | Safe statements about scope, missing data, or uncertainty |

Each `results[]` object contains:

| Field | Type | Requirement |
|---|---|---|
| `collector_name` | Identifier string | Exact registered collector name |
| `collector_version` | Identifier string | Collector contract/implementation version |
| `status` | String | `succeeded`, `unavailable`, `failed`, or `timed_out` |
| `started_at` | Timestamp | Timezone-aware collector start time |
| `completed_at` | Timestamp | Timezone-aware collector completion time |
| `duration_ms` | Integer | Non-negative duration |
| `evidence` | Array | Existing `Evidence` objects; empty unless the result succeeded |
| `provenance` | Array | One matching record for every evidence item |
| `errors` | Array | Empty on success; otherwise at least one safe error |

Each `evidence[]` object contains the existing fields:

- `evidence_id`
- `kind`
- `name`
- `value`
- `unit`
- `observed_at`
- `source`

Each `provenance[]` object contains:

- `evidence_id`
- `collector_name`
- `collector_version`
- `source_type`: `procfs`, `filesystem_stat`, `runtime_api`, or `derived`
- `source_ref`: normalized reference from Section 9
- `read_only`: always `true`

Each `errors[]` object contains:

- `code`: stable machine-readable identifier
- `message`: safe caller-facing summary
- `retryable`: boolean

### 10.3 HTTP status and error behavior

| HTTP status | Condition | Body |
|---|---|---|
| `200 OK` | Snapshot status is `succeeded` or `partial` | `EvidenceSnapshot` |
| `415 Unsupported Media Type` | Request is not JSON | Existing `ErrorResponse` |
| `422 Unprocessable Entity` | Contract validation, unknown/disabled/duplicate collector, or unsupported target fails | Existing `ErrorResponse`; no collector runs |
| `503 Service Unavailable` | Snapshot status is `failed` | Failed `EvidenceSnapshot` with safe collector errors and audit ID |
| `500 Internal Server Error` | Unmapped internal or required audit failure | Existing safe `ErrorResponse` |

The existing `ErrorResponse` fields remain:

- `schema_version`
- `error_code`
- `message`
- `correlation_id`
- `details[]`, containing `location`, `message`, and `problem_type`

Stable collection error codes include:

- `request_validation_failed`
- `unsupported_media_type`
- `collector_unknown`
- `collector_disabled`
- `collector_unavailable`
- `collector_failed`
- `collector_timed_out`
- `target_unsupported`
- `collection_failed`
- `internal_error`

### 10.4 Analysis reuse and evidence interpretation

Successful `results[].evidence` objects shall be copied unchanged into the existing incident request's `evidence` array. Provenance remains part of the collection snapshot; the shared evidence ID and source retain the link between the snapshot and analysis.

Relevant evidence is fresh when its `observed_at` value is no more than five minutes before `Incident.occurred_at` and no more than 30 seconds after it. Evidence outside that range shall not support a definitive hypothesis and shall produce a limitation.

For `signal_type=high_cpu`:

| `system_load_1m_per_cpu` | Required interpretation |
|---|---|
| `>= 1.00` | Strong evidence of load pressure; do not call it measured CPU utilization |
| `>= 0.70` and `< 1.00` | Elevated load with bounded confidence |
| `< 0.70` | Current load evidence does not confirm saturation; lower confidence and add a limitation |

For `signal_type=low_disk_space`:

| `disk_used_percent` | Required interpretation |
|---|---|
| `>= 90` | Strong evidence of disk pressure |
| `>= 80` and `< 90` | Elevated disk use with bounded confidence |
| `< 80` | Current evidence does not confirm low disk space; lower confidence and add a limitation |

`disk_free_bytes` may support the disk hypothesis when present. Memory evidence does not create a new incident type in Week 2 and must not be used to invent an unrelated cause.

### 10.5 Safe logging allow-list

Collection logs may contain only necessary safe metadata:

- Timestamp and level
- Service and event name
- Correlation and collection IDs
- Target type, but not caller-supplied descriptions or arbitrary payloads
- Collector name and status
- Duration and evidence count
- Stable safe error code

Evidence values, raw source content, complete requests/responses, environment mappings, machine-specific paths, and exception arguments are not logged by default.

## 11. Failure and partial-success behavior

| Condition | Collector result | Snapshot/API behavior | Required safety behavior |
|---|---|---|---|
| All requested collectors succeed | `succeeded` for each | `succeeded`, HTTP 200 | Return evidence and matching provenance |
| At least one succeeds and another is unavailable/fails/times out | Mixed statuses | `partial`, HTTP 200 | Preserve successes; include safe errors and limitations |
| No collector succeeds | Non-success for each | `failed`, HTTP 503 | Return no fabricated evidence; include audit ID and safe errors |
| Unknown collector requested | No result | HTTP 422 `collector_unknown` | Run no collector |
| Registered but disabled collector requested | No result | HTTP 422 `collector_disabled` | Run no collector |
| Duplicate collector requested | No result | HTTP 422 validation error | Run no collector |
| Unsupported target requested | No result | HTTP 422 `target_unsupported` | Run no collector |
| One collector exceeds its deadline | `timed_out` | Partial or failed based on other results | Stop/contain that operation; preserve other results |
| Source file is absent or inaccessible | `unavailable` | Partial or failed | Do not substitute a value or reveal the path |
| Source data is malformed or inconsistent | `failed` | Partial or failed | Do not return partially parsed evidence |
| Provenance cannot be constructed | `failed` | Partial or failed | Do not return unprovenanced evidence |
| Required audit event cannot be recorded | No successful completion | Safe HTTP 500 | Do not claim success without audit evidence |
| Unexpected internal exception | Mapped at boundary | Safe HTTP 500 with correlation ID | Redact details; no stack trace in response |

## 12. Acceptance scenarios

### 12.1 Successful collection

**Given** the three Linux collectors are registered and enabled and their approved sources are valid  
**When** the user requests `linux.load`, `linux.memory`, and `linux.disk`  
**Then** the API returns HTTP 200, a `succeeded` snapshot, three ordered successful results, required evidence and provenance, matching correlation IDs, and an audit event ID.

### 12.2 Partial collection

**Given** load and disk sources are valid and memory is unavailable  
**When** the user requests all three collectors  
**Then** the API returns HTTP 200, a `partial` snapshot, preserves load and disk evidence, reports a safe memory error, and states the limitation.

### 12.3 Total collection failure

**Given** every requested approved source is unavailable or fails  
**When** collection runs  
**Then** the API returns HTTP 503, a `failed` audited snapshot, no fabricated evidence, and one safe result per collector.

### 12.4 Invalid or disabled collector

**Given** the request names an unknown or disabled collector  
**When** the API validates the request  
**Then** it returns HTTP 422 with the stable error contract and invokes no collector.

### 12.5 Collector timeout

**Given** one fake collector exceeds its independent configured timeout while another succeeds  
**When** the collection service runs  
**Then** the slow collector returns `timed_out`, the successful evidence remains available, and the snapshot is `partial`.

### 12.6 Evidence reuse in analysis

**Given** a successful collection snapshot contains fresh `system_load_1m_per_cpu` evidence  
**When** the unchanged evidence object is placed in a valid high-CPU incident and submitted to analysis  
**Then** the resulting hypotheses and recommendations cite its evidence ID and apply the documented thresholds.

### 12.7 Stale or contradictory evidence

**Given** relevant evidence is stale, future-dated, or below the threshold implied by the incident signal  
**When** the incident is analyzed  
**Then** confidence is reduced, uncertainty is stated, and OpsPilot does not fabricate confirmation.

### 12.8 Attempted path injection

**Given** a caller adds a path or arbitrary collector parameter to the request  
**When** the API validates it  
**Then** strict schema validation returns HTTP 422 before collection begins.

### 12.9 Required audit failure

**Given** the collection completes but the required audit sink fails  
**When** the API prepares the response  
**Then** it returns a safe failure response and does not report a successful collection.

### 12.10 Clean-clone demonstration

**Given** a contributor has only the documented prerequisites and a clean clone  
**When** they run the Week 2 setup, verification, service, and demo commands  
**Then** all documented success, partial, rejection, and analysis-reuse steps complete without cloud credentials, external network access, or elevated privileges.

## 13. Assumptions and constraints

- Linux procfs is available for the local/container runtime; unsupported platforms report collectors as unavailable.
- Measurements describe the OpsPilot process's runtime namespace.
- One API process and in-memory request-scoped state are sufficient.
- Collection is initiated explicitly by an API request; Week 2 adds no scheduler or background polling.
- The maximum request contains three collectors.
- The default collector timeout is two seconds, with a hard configuration maximum of 30 seconds.
- Disk paths are owned by validated operator configuration and cannot be selected by API callers.
- The existing `Evidence` contract remains the interchange format for analysis.
- The existing deterministic analyzer remains pure and performs no collection I/O.
- Synthetic incident metadata is still used even when local runtime measurements are real.
- Existing Week 1 quality, security, container, and audit controls continue to apply.

## 14. Resolved requirement decisions

| Question | Decision | Rationale |
|---|---|---|
| Which Linux sources are approved? | `/proc/loadavg`, required `/proc/meminfo` keys, Python CPU count, and standard-library disk statistics for configured paths only | They provide the required evidence without commands, sockets, networks, or new privileges |
| Is the observed scope the container or physical host? | The runtime/container namespace visible to OpsPilot | This is the only scope the process can truthfully guarantee without a privileged host integration |
| How are partial results represented? | An `EvidenceSnapshot` with `status=partial`, HTTP 200, one result per collector, successful evidence preserved, and safe errors/limitations included | Partial evidence remains useful when failure is explicit |
| What happens when every collector fails? | Return a valid audited snapshot with `status=failed` and HTTP 503 | The caller receives structured failure evidence without false success |
| Who chooses disk paths? | The operator through validated startup configuration; default `/` | API callers must not gain arbitrary filesystem-read capability |
| What is the maximum collector timeout? | 30 seconds; default 2.0 seconds; accepted range 0.1–30.0 seconds | It provides a bounded local operation and testable configuration |
| Which fields may be logged? | Only the safe metadata allow-list in Section 10.5 | Raw measurements and source contents are unnecessary for operational tracing |
| How is evidence transferred into analysis? | Copy successful `results[].evidence` objects unchanged into `Incident.evidence` | This preserves the existing contract and keeps collection outside the analyzer |

## 15. Unresolved questions

| Question | Owner | Resolution point | Blocking? |
|---|---|---|---|
| Should collector execution be sequential or bounded-concurrent? | Architecture owner | ADR-0004 in #32 | Blocks #34 until decided |
| What exact cancellation mechanism guarantees a timed-out collector cannot continue mutating in-memory request state? | Collection-service owner | #34 design and timeout tests | Blocks #34 implementation |
| Should additional configured disk paths be permitted in Week 2 or deferred until stable public resource identifiers are designed? | Requirements and architecture owners | #32 before #35 | Blocks additional paths, not the default root path |
| Should collection readiness validate source availability or only registry/configuration validity? | API and architecture owners | #32 and #36 | Does not block contracts; must be decided before readiness changes |

An unresolved question blocks only the named dependent behavior. It does not permit an implementation to choose a broader or less safe default silently.

## 16. Requirements traceability

### 16.1 Epic exit-criterion coverage

| Epic #30 exit criterion | Governing requirements |
|---|---|
| Stable, testable requirements and issue mapping | This document; Section 16.2 |
| Documented collector architecture and trust boundaries | `COL-FR-004`, `COL-FR-011`–`COL-FR-014`, `COL-SAFE-001`–`COL-SAFE-009` |
| Versioned request, result, evidence, provenance, and error contracts | `COL-FR-002`, `COL-FR-009`, `COL-FR-010`, `COL-FR-012`–`COL-FR-017`, `COL-NFR-009` |
| Only registered and enabled collectors run | `COL-FR-004`, `COL-SAFE-004`, `COL-SAFE-015` |
| Linux load, memory, and disk collection without commands | `COL-FR-006`–`COL-FR-008`, `COL-SAFE-002`, `COL-SAFE-009` |
| Collection API returns documented fields and status codes | `COL-FR-001`, `COL-FR-002`, `COL-FR-013`–`COL-FR-017`, Section 10 |
| Success, partial, failure, invalid, unsupported, and timeout behavior is tested | `COL-FR-011`–`COL-FR-014`, `COL-FR-017`, Section 12 |
| Collected evidence influences deterministic triage | `COL-FR-018`–`COL-FR-021` |
| Collection emits structured logs and audit events with redaction | `COL-FR-015`, `COL-FR-016`, `COL-NFR-011`, `COL-SAFE-011`–`COL-SAFE-016` |
| Container and CI preserve runtime hardening | `COL-NFR-012`–`COL-NFR-015`, `COL-SAFE-005`, `COL-SAFE-006` |
| A contributor can reproduce the demonstration | `COL-FR-025`, `COL-NFR-016` |
| Full local and CI verification passes | `COL-NFR-001`–`COL-NFR-003`, `COL-NFR-012`, `COL-NFR-013` |

### 16.2 Implementation and verification allocation

| Requirement group | Implementation issue | Primary evidence |
|---|---|---|
| Architecture boundaries; `COL-SAFE-001`–`COL-SAFE-009`, `COL-SAFE-017`, `COL-SAFE-018` | [#32](https://github.com/standardforever/ops_pilot/issues/32) | Architecture document, ADR-0004, trust-boundary review |
| `COL-FR-002`, `COL-FR-003`, `COL-FR-005`, `COL-FR-009`, `COL-FR-010`, `COL-FR-012`–`COL-FR-014`, `COL-FR-018`, `COL-NFR-009`, `COL-NFR-010` | [#33](https://github.com/standardforever/ops_pilot/issues/33) | Domain fixtures, schema tests, invariant tests |
| `COL-FR-004`, `COL-FR-005`, `COL-FR-011`–`COL-FR-014`, `COL-FR-022`, `COL-FR-024`, `COL-NFR-003`–`COL-NFR-008`, `COL-SAFE-004`, `COL-SAFE-015` | [#34](https://github.com/standardforever/ops_pilot/issues/34) | Registry, configuration, orchestration, timeout, and isolation tests |
| `COL-FR-006`–`COL-FR-010`, `COL-FR-014`, `COL-NFR-002`, `COL-NFR-003`, `COL-SAFE-002`, `COL-SAFE-009`, `COL-SAFE-010`, `COL-SAFE-014` | [#35](https://github.com/standardforever/ops_pilot/issues/35) | Fixture-backed parser/collector tests and source review |
| `COL-FR-001`–`COL-FR-005`, `COL-FR-012`–`COL-FR-017`, `COL-FR-022`, `COL-FR-023`, `COL-NFR-017`, `COL-SAFE-003` | [#36](https://github.com/standardforever/ops_pilot/issues/36) | API, content-type, OpenAPI, error, and correlation tests |
| `COL-FR-018`–`COL-FR-021`, `COL-FR-024`, `COL-SAFE-018` | [#37](https://github.com/standardforever/ops_pilot/issues/37) | Analyzer boundary, stale-evidence, reference-integrity, and integration tests |
| `COL-FR-015`, `COL-FR-016`, `COL-NFR-011`, `COL-NFR-017`, `COL-SAFE-011`–`COL-SAFE-016` | [#38](https://github.com/standardforever/ops_pilot/issues/38) | Log capture, audit sink, recursive-redaction, and fault-injection tests |
| `COL-NFR-001`–`COL-NFR-017`, all `COL-SAFE` controls | [#39](https://github.com/standardforever/ops_pilot/issues/39) | `make verify`, coverage, static security, CI, image inspection, and smoke evidence |
| `COL-FR-025`, `COL-NFR-016`, Section 12 acceptance scenarios | [#40](https://github.com/standardforever/ops_pilot/issues/40) | Clean-clone runbook and executable Week 2 demonstration |

## 17. Approval criteria

This requirements document is ready for architecture and implementation when:

- Every requirement has a stable ID and verification method.
- Every Epic #30 exit criterion maps to one or more requirements.
- Every requirement group maps to an implementation issue and evidence type.
- Approved source data, mechanisms, derived values, names, and units are explicit.
- Prohibited sources, inputs, privileges, and behaviors are explicit.
- Request, response, status, error, partial-success, and total-failure behavior are unambiguous.
- Container/runtime scope is stated without implying physical-host visibility.
- Evidence reuse and deterministic analysis thresholds are testable.
- No requirement depends on AWS, Kubernetes, Terraform, Ansible, an external AI provider, production infrastructure, or elevated privileges.
- Blocking architecture questions have named owners and resolution points.
- Issue #31 is reviewed before implementation of Issues #32–#40 proceeds.
