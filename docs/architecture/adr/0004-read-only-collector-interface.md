# ADR-0004: Use a Static Asynchronous Read-Only Collector Interface

- **Status:** Proposed
- **Date:** 2026-09-23
- **Decision owners:** Project maintainers
- **Related issue:** [#32](https://github.com/standardforever/ops_pilot/issues/32)
- **Requirements:** [Week 2 requirements](../../requirements/week-02.md)
- **Architecture:** [Evidence collection](../evidence-collection.md)

## Context

OpsPilot needs to collect real operational evidence without creating an execution
or arbitrary-code-loading path. Week 2 adds local Linux load, memory, and disk
collectors. Later stages may add AWS, Kubernetes, and observability providers.

The interface must support different I/O mechanisms, independent deadlines,
partial success, deterministic results, and test doubles. At the same time, an API
caller or environment setting must not be able to select a Python module, command,
filesystem path, or implementation object.

The existing deterministic analyzer accepts validated `Evidence` objects and must
remain independent from collection I/O.

## Decision drivers

- Preserve the read-only and no-execution security boundary
- Prevent caller-controlled or configuration-controlled code loading
- Support local and future network-bound observation without changing the domain
- Enforce an independent deadline for every collector
- Isolate failures and retain successful sibling results
- Preserve deterministic output order under concurrency
- Keep evidence compatible with the existing incident contract
- Make operating-system and provider I/O replaceable in tests
- Represent absence and failure without fabricated values
- Keep provider SDK types outside domain and analysis components

## Considered options

### Static asynchronous collectors with bounded concurrency

Collectors implement an async protocol, are constructed explicitly at startup,
and are stored in an immutable registry. The collection service runs requested
collectors under independent deadlines with a bound no greater than the request
maximum. Results are assembled by request index.

Advantages:

- Supports cancellation and network-bound providers naturally
- Avoids additive latency across independent collectors
- Keeps implementation selection under reviewed application code
- Allows independent timeout and failure mapping
- Preserves deterministic output with explicit ordering

Disadvantages:

- Requires careful cancellation and late-result containment
- Adds orchestration complexity compared with a sequential loop
- Blocking operating-system reads need a narrow adapter or worker thread

### Static synchronous collectors executed sequentially

Collectors expose a regular function and the service calls them one at a time.

Advantages:

- Simple control flow
- Completion order is naturally deterministic

Disadvantages:

- Total latency is the sum of collector latency
- Python cannot reliably interrupt a blocked synchronous call
- Future provider I/O would require another interface or service-level thread pool
- One slow call delays all subsequent collectors

### Dynamic plugin discovery

Collectors are discovered through import strings, Python entry points, a plugin
directory, or reflection.

Advantages:

- Third parties can add collectors without changing the application wiring
- Provider packages can be deployed independently

Disadvantages:

- Configuration becomes an arbitrary code-loading mechanism
- Installed packages can silently expand runtime behavior
- Registration, review, provenance, and dependency control become weaker
- Failure and security behavior is harder to verify as a closed set

### Provider-specific services and response models

Each source exposes its own API, response shape, and analysis integration.

Advantages:

- Provider teams can optimize independently

Disadvantages:

- Couples analysis to provider SDKs and transport models
- Duplicates timeout, failure, audit, and redaction behavior
- Makes evidence reuse and cross-provider testing inconsistent

## Decision

Use a static, asynchronous, read-only `Collector` interface with bounded
concurrent orchestration and immutable domain results.

### Interface shape

The logical protocol is:

```python
class Collector(Protocol):
    @property
    def descriptor(self) -> CollectorDescriptor: ...

    async def collect(self, context: CollectionContext) -> CollectorPayload: ...
```

`CollectorDescriptor`, `CollectionContext`, and `CollectorPayload` are strict,
immutable domain types. They do not depend on FastAPI or a provider SDK.

The collector returns either:

- a complete payload containing evidence and exactly one provenance record for
  every evidence ID; or
- a typed unavailable/failure signal that the collection service maps to a safe
  `CollectorResult`.

The collector does not own aggregate status, HTTP mapping, correlation policy,
audit completion, or result ordering.

### Asynchronous bounded execution

The interface is asynchronous because future collectors will be I/O-bound and
need cooperative cancellation. The service may run the one to three requested
collectors concurrently. Concurrency is request-scoped and bounded by the
validated request maximum; collectors cannot spawn unbounded background work.

The service creates tasks in request order, records the index with each task, and
assembles results by that index after tasks terminate. Completion timing therefore
cannot change the response order.

### Static registration

The application composition root constructs every approved collector explicitly
and passes the instances into an immutable registry. Configuration contains only
stable collector names that may enable a subset of this compiled set.

The design rejects:

- Runtime module or package discovery
- Python entry-point discovery
- Caller-supplied or configuration-supplied import paths
- Plugin directories
- Reflection-based collector construction
- Registration or upload APIs

Adding an implementation requires a code review, locked dependency update where
needed, explicit composition-root change, and tests.

### Per-collector timeout

The collection service wraps each `collect` call in an independent async deadline
using validated startup configuration. A timeout cancels the task and publishes a
`timed_out` result. The service never publishes a payload received after the
deadline.

Collectors must cooperate with async cancellation. A future provider client must
also receive an internal request timeout no greater than the remaining service
deadline.

A blocking operating-system call may finish after its waiting task is cancelled.
Containment, rather than unsafe thread termination, is guaranteed:

- The operation is read-only.
- Inputs and outputs are request-scoped and immutable.
- The collector has no reference to the aggregate result or audit sink.
- Only the service may publish payloads.
- Late payloads are discarded.
- Collectors may not mutate global or shared request state.

### Deterministic ordering

The request order is authoritative. Registry lookup preserves the requested name
sequence, tasks retain their request index, and the final result tuple is sorted by
that index. Dictionary iteration order, registry order, and completion order do
not define the public response.

### Provenance

Every evidence item has exactly one `EvidenceProvenance` record with:

- `evidence_id`
- `collector_name`
- `collector_version`
- `source_type`
- normalized `source_ref`
- `read_only=true`

The payload is invalid unless evidence IDs and provenance evidence IDs form a
one-to-one set. Raw source paths and provider payloads are not provenance.

### Disk path ownership

Disk paths come from validated operator configuration, not API input. The default
is `/`. This keeps filesystem scope under deployment control and prevents an API
caller from turning the disk collector into an arbitrary path-probing interface.

Additional paths remain disabled until a stable public resource-identifier
contract prevents machine-specific paths from leaking through responses, logs, or
provenance.

### Evidence compatibility

Successful collector payloads use the existing `Evidence` domain model. A caller
can copy `results[].evidence` unchanged into `Incident.evidence`.

The analyzer receives evidence only. It does not receive a collector, registry,
source reader, collection context, or provider SDK object. It remains a pure,
deterministic function over validated domain data.

### Unavailable data

Expected absence or inaccessibility is represented as a typed unavailable
outcome. The service returns `status=unavailable`, an empty evidence/provenance
collection, and a stable safe error.

A collector must never substitute zero, a default measurement, a cached guess, or
an inferred value for missing, malformed, inconsistent, inaccessible, timed-out,
or non-finite source data.

## Consequences

### Positive

- The API can select only reviewed collector names, never implementation code.
- Local and future provider collectors share one result and provenance boundary.
- Independent work can complete concurrently without changing public ordering.
- A failed or timed-out collector does not discard successful siblings.
- The analyzer stays independent from I/O and provider dependencies.
- Tests can replace clocks, IDs, readers, registry entries, collectors, and audit
  sinks without using the current machine state.
- Read-only late work can be contained safely without unsafe thread termination.

### Negative

- The service needs explicit task, timeout, exception, and ordering logic.
- Collector authors must understand cancellation and immutable result rules.
- Synchronous operating-system APIs need narrow adapters and cannot always be
  interrupted once entered.
- A new collector requires an application release instead of runtime installation.
- Provider-specific optimizations must remain behind the common domain contract.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A timed-out blocking read completes later | Read-only operation, immutable local state, no aggregate reference, and discard-after-deadline rule |
| One task failure cancels siblings | Capture failures at each task boundary and aggregate terminal outcomes independently |
| Concurrency makes output nondeterministic | Attach request index before scheduling and assemble by index |
| A collector returns partial or unmatched provenance | Validate the complete payload atomically before publishing it |
| Configuration enables unknown behavior | Resolve enabled names against the closed registry at startup and fail readiness |
| A future provider leaks SDK types into analysis | Require normalization to `Evidence` and prohibit SDK imports in domain/analyzer packages |
| Caller expands filesystem scope | Keep paths out of the API and validate deployment-owned configuration |
| Dynamic plugin loading is added for convenience | Static security tests and architecture review reject imports, entry points, and plugin directories |
| Raw values leak through telemetry | Safe-field allow-list, central recursive redaction, and log/audit tests |
| Async collectors create background tasks | Prohibit unowned tasks and require all work to terminate or be contained by the service deadline |

## Validation

The decision is implemented correctly when tests prove that:

- Duplicate, unknown, disabled, or unsupported names start no collectors.
- Only explicitly registered instances can be resolved.
- Collectors completing out of order still produce request-ordered results.
- Each collector receives an independent deadline.
- Success, unavailable, failure, timeout, and unexpected exception outcomes map to
  the documented result states.
- A timed-out or cancelled collector cannot publish a late result or mutate the
  aggregate.
- One collector failure does not corrupt or discard sibling success.
- Evidence and provenance form a one-to-one relationship.
- Collected evidence validates unchanged inside `Incident.evidence`.
- The analyzer imports no collector, registry, reader, or provider package.
- Disk paths cannot be supplied through the API.
- Static checks find no subprocess, dynamic import, entry-point discovery, Docker
  socket, privilege, or mutation path in the collection package.
- Tests use injected sources and run without internet access or current host values.

## Revisit conditions

Revisit this decision if:

- A collector requires CPU-bound work that cannot safely share the API process.
- Provider quotas require a cross-request worker pool, queue, or scheduler.
- Collection must survive process restart or provide durable job status.
- The maximum collector count grows enough that a fixed request-local bound is no
  longer operationally appropriate.
- A trusted extension ecosystem is required and can provide signed artifacts,
  capability declarations, isolation, policy, provenance, and revocation.
- Stable multi-path disk resource identifiers are approved.
- Evidence provenance needs durable storage or cryptographic attestation.

Any change to runtime discovery, execution isolation, persistence, credentials, or
mutation requires a new or superseding ADR and threat-model review.

