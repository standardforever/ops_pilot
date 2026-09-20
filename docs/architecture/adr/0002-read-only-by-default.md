# ADR-0002: Make OpsPilot Read-Only by Default

- **Status:** Proposed
- **Date:** 2026-09-20
- **Decision owners:** Project maintainers
- **Related issue:** [#3](https://github.com/standardforever/ops_pilot/issues/3)

## Context

OpsPilot is intended to analyze infrastructure incidents and may eventually propose or coordinate operational actions. Infrastructure mutation introduces significant security, reliability, authorization, and accountability risks.

Allowing execution before evidence, policy, approval, audit, verification, and rollback boundaries exist would create an unsafe architecture that is difficult to correct later.

## Decision drivers

- Minimize blast radius during early development
- Establish explainability before automation
- Keep credentials outside the initial trust boundary
- Make testing deterministic and reproducible
- Preserve separation between recommendation and authorization
- Allow security controls to mature before privileged integrations exist

## Considered options

### Read-only analysis first

The system validates incidents, analyzes synthetic evidence, and returns action proposals without execution.

Advantages:

- Small trust boundary
- No production credentials
- Clear separation of analysis and execution
- Easier deterministic testing

Disadvantages:

- Does not demonstrate end-to-end remediation
- Execution interfaces must be designed and implemented later

### Introduce a sandbox executor immediately

The system can execute a limited set of commands inside an isolated environment.

Advantages:

- Demonstrates automation earlier

Disadvantages:

- Encourages command-shaped action contracts
- Adds sandbox, authorization, and escape risks before core boundaries are proven
- Can create an architectural shortcut that later reaches production

### Connect directly to a development cloud account

Advantages:

- Provides realistic external-system behavior

Disadvantages:

- Requires credentials, cost controls, cleanup, policy, and blast-radius management
- Reduces local reproducibility
- Makes the first slice dependent on external state

## Decision

OpsPilot is read-only by default.

The initial system:

- Uses synthetic incidents and evidence
- Does not load cloud or Kubernetes credentials
- Does not execute shell commands or scripts
- Does not modify local or remote infrastructure
- Represents proposed actions only as validated data
- Requires every proposed action to declare `read_only`, `risk_level`, and `requires_approval`
- Rejects unsupported or mutating action types

Future mutation requires separate policy, approval, execution, verification, and rollback components. Adding an executor requires a new ADR and threat model.

## Consequences

### Positive

- A compromised or incorrect analyzer cannot directly modify infrastructure.
- The project can validate evidence and decision quality before granting privilege.
- Local testing requires no external accounts or secrets.
- Action contracts can be designed independently from shell commands.

### Negative

- Early releases provide recommendations rather than remediation.
- Some operational assumptions cannot be proven until a bounded executor exists.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Contributors bypass the boundary for a demo | CI, code review, dependency review, and explicit safety requirements |
| Action proposals are mistaken for approval | Separate types and explicit documentation |
| Future executor reuses unsafe string commands | Require an allow-listed, typed action catalog |

## Exit criteria for future execution

Execution may be considered only after the project has:

- A versioned, allow-listed action catalog
- Independent policy evaluation
- Authenticated approval with scope and expiry
- Least-privilege, short-lived workload credentials
- Idempotency and concurrency controls
- Structured audit events
- Post-action verification
- Rollback or compensating procedures
- A threat model and failure-injection tests

## Validation

- Static review finds no shell, cloud, Kubernetes, or remote execution path.
- Tests run offline without infrastructure credentials.
- Domain validation rejects unsupported mutating actions.
- The architecture diagram contains no reachable execution component in the initial request path.
