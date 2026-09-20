# ADR-0001: Use Python, FastAPI, and Pydantic for the Initial Service

- **Status:** Proposed
- **Date:** 2026-09-20
- **Decision owners:** Project maintainers
- **Related issue:** [#3](https://github.com/standardforever/ops_pilot/issues/3)

## Context

OpsPilot requires a typed HTTP API, strict input and output validation, deterministic analysis rules, automated testing, and a path toward future automation and AI-assisted components.

The initial implementation should be easy to run locally, quick to test, and explicit about domain contracts. The project does not yet require the throughput or static single-binary deployment characteristics that would justify optimizing for a lower-level runtime.

## Decision drivers

- Strong ecosystem for operations automation and future AI integration
- Clear request, response, and domain validation
- Generated OpenAPI documentation
- Mature unit and API testing tools
- Static type checking support
- Low setup cost for the first service slice
- Compatibility with Docker and future Kubernetes deployment

## Considered options

### Python with FastAPI and Pydantic

Advantages:

- Direct typed API development
- Pydantic provides reusable domain and transport validation
- FastAPI generates OpenAPI from the declared contracts
- Strong pytest ecosystem
- Natural fit for automation, cloud SDKs, and later model evaluation

Disadvantages:

- Runtime type safety depends on validation and static analysis discipline
- Packaging and dependency management require an explicit standard
- CPU-bound workloads may require different execution strategies later

### Go with `net/http` or a web framework

Advantages:

- Strong compile-time guarantees
- Simple static deployment artifact
- Good concurrency and cloud-native ecosystem

Disadvantages:

- Slower iteration for the project's expected analysis and AI experimentation
- More manual schema and validation plumbing for the first slice

### TypeScript with Node.js

Advantages:

- Strong developer tooling and broad web ecosystem
- Shared language if a web interface is introduced

Disadvantages:

- Less direct alignment with the expected infrastructure-analysis and AI tooling
- Runtime schema validation still requires a separate disciplined model

## Decision

Use Python 3.12 or later for the initial service, with:

- FastAPI for HTTP routing and OpenAPI generation
- Pydantic for configuration, request, response, and domain validation
- pytest for tests
- Ruff for formatting and linting
- mypy for static type checking

Domain models must not import FastAPI. HTTP transport code maps validated domain objects to and from API schemas without embedding business rules in route handlers.

## Consequences

### Positive

- The project can establish validated contracts quickly.
- Deterministic analysis and future model evaluation can share Python tooling.
- OpenAPI provides immediate interface documentation.
- Local and container development remain straightforward.

### Negative

- The project must enforce typing, linting, and tests in CI.
- Dependency and packaging choices must be documented and reproducible.
- Performance-sensitive components may later require profiling or a different implementation language.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Business logic leaks into route handlers | Enforce service and domain boundaries through structure and review |
| Invalid data bypasses expected typing | Validate all external input with Pydantic and test boundary cases |
| Dependency sprawl | Maintain small dependency groups and automated vulnerability scanning |
| Type regressions | Run mypy in local verification and CI |

## Validation

This decision is validated when the service can:

- Generate the documented OpenAPI contract
- Reject invalid incident and action models
- Run all unit and API tests offline
- Pass formatting, linting, and type checks
- Build and run in a non-root Docker container

## Revisit conditions

Reconsider this decision if measured production requirements demonstrate that Python cannot satisfy required latency, throughput, resource use, packaging, or isolation constraints.
