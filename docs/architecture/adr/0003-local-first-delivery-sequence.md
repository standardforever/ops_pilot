# ADR-0003: Use a Local-First Delivery Sequence

- **Status:** Proposed
- **Date:** 2026-09-20
- **Decision owners:** Project maintainers
- **Related issue:** [#3](https://github.com/standardforever/ops_pilot/issues/3)

## Context

The target OpsPilot platform includes AWS, Terraform, Kubernetes, Helm, Prometheus, Grafana, Argo CD, and security controls. Implementing all of those systems before proving the product and domain contracts would create cost and complexity without validating the core incident-analysis workflow.

The project needs a delivery order that produces usable evidence at each stage and prevents infrastructure from becoming the product definition.

## Decision drivers

- Fast feedback on product and domain design
- Reproducible contributor environment
- No cloud cost or account dependency for core tests
- Small failure and security surface
- Clear contracts before distributed-system integration
- An incremental path to the target cloud-native architecture

## Considered options

### Local-first vertical slice

Build and test the API, domain contracts, deterministic analysis, audit output, container, and CI locally before adding cloud integrations.

Advantages:

- Proves the user-visible workflow early
- Creates contracts that later adapters must follow
- Keeps tests fast and offline
- Reduces credential and cost risk

Disadvantages:

- Distributed-system behavior is deferred
- Some deployment assumptions remain untested initially

### Infrastructure-first platform

Provision AWS and Kubernetes before implementing the analysis workflow.

Advantages:

- Establishes the target runtime early

Disadvantages:

- High setup cost before product validation
- Slow feedback and harder contributor onboarding
- Encourages placeholder services designed around infrastructure rather than requirements

### Cloud-service prototype

Use managed cloud services directly for a quick demonstration.

Advantages:

- Can demonstrate integration rapidly

Disadvantages:

- Creates external state and credential dependencies
- Reduces reproducibility
- Can obscure core contracts behind provider-specific behavior

## Decision

Use a local-first delivery sequence:

1. Requirements, architecture, and repository controls
2. Local API and versioned domain contracts
3. Deterministic read-only analysis and audit output
4. Docker, tests, CI, and security baseline
5. Read-only evidence collectors
6. AWS infrastructure provisioned with Terraform
7. Kubernetes and Helm runtime packaging
8. Prometheus/Grafana observability and Argo CD delivery
9. Independent policy and approval services
10. Bounded execution, verification, and rollback
11. Evaluated AI-assisted analysis and operations

Ansible may be introduced only where host or configuration automation is required and neither Terraform nor Kubernetes reconciliation is the correct owner.

## Consequences

### Positive

- Every platform layer is introduced in response to a proven responsibility.
- Contributors can develop core behavior without an AWS account.
- Cloud and Kubernetes adapters implement stable contracts rather than defining them.
- Security controls evolve with the privilege being introduced.

### Negative

- Production deployment occurs later in the project.
- Local assumptions must be revalidated when distributed components are introduced.
- Interfaces may require revision as real integrations reveal constraints.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Local design does not scale to distributed execution | Keep component interfaces explicit and review them at each architecture increment |
| Infrastructure work is postponed indefinitely | Track entry and exit criteria for each stage |
| The local implementation becomes a monolith | Preserve domain, analysis, audit, policy, and adapter boundaries in code |

## Validation

The sequence is working when:

- Core tests run without cloud accounts or external network access.
- Each later integration maps to an existing interface and requirement.
- Infrastructure changes do not require rewriting the product contract.
- A stage is introduced only after the preceding stage has reproducible verification evidence.

## Revisit conditions

Revisit this decision if a core product requirement cannot be validated locally or if a provider constraint requires an earlier architectural decision. Such a change must be documented in a superseding ADR.
