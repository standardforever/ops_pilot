# Week 1 Threat Model

## System boundary

The assessed system is the local OpsPilot API, deterministic analyzer, structured logging and audit output, dependency supply chain, container image, and contributor/CI workflow. It accepts only synthetic incidents and has no infrastructure credentials or execution adapter.

## Assets

- Integrity of analysis rules and safety invariants
- Integrity of source, dependencies, CI workflows, and container image
- Availability of the local API and development workflow
- Confidentiality of future operational context and contributor environments
- Audit and correlation metadata used to explain decisions

## Trust boundaries

| Boundary | Untrusted input | Existing control |
|---|---|---|
| HTTP client to API | Headers and JSON body | Strict schema, enums, size-constrained fields, sanitized 4xx errors |
| API to analyzer | Validated incident | Framework-independent immutable models and pure deterministic rules |
| Analyzer to action proposal | Rule output | Allow-listed action enum and `read_only=true` literal |
| Application to logs | Operational metadata | Central redaction; no full incident payload logging |
| Repository to CI | Source, workflow, dependency changes | Review, immutable action SHAs, read-only token, automated gates |
| Registry to image | Base image and Python packages | Version pinning, lockfile, vulnerability scan, minimal final stage |
| Container to host | Process and network exposure | Non-root UID, loopback port, dropped capabilities, read-only filesystem |

## Threats, mitigations, and residual risk

| Threat | Impact | Mitigations | Residual risk / next control |
|---|---|---|---|
| Malformed or adversarial incident | Crash, misleading plan, resource use | Strict request contract, bounded strings, fail-closed enums, safe errors | Add explicit request-byte and rate limits before network deployment |
| Analyzer fabricates certainty | Unsafe operator decision | Deterministic rules, evidence references, bounded confidence, unknown fallback | Future AI output requires evaluation, grounding, and policy review |
| Mutating action enters the contract | Infrastructure change becomes reachable | Literal read-only invariant, allow-listed action types, no executor or SDK | Any executor requires a new ADR, threat model, approval, and rollback design |
| Secret leaks through source or logs | Credential compromise | Gitleaks, detect-secrets, redaction tests, synthetic fixtures, private reporting | Add provider-native secret scanning and DLP when credentials are introduced |
| Malicious or vulnerable dependency | Build or runtime compromise | Lockfile, minimal dependencies, pip-audit, Dependabot, Trivy | Add provenance/SBOM signing and trusted publishing before releases |
| Compromised CI action | Token or source compromise | Immutable SHAs, read-only permissions, documented update review | Introduce organization allowlists and artifact attestations later |
| Container escape or host modification | Host compromise | Non-root, dropped capabilities, no-new-privileges, read-only root | Apply Kubernetes seccomp/AppArmor and network policy at that stage |
| Log injection or sensitive error | Misleading audit or data disclosure | JSON encoding, safe structured fields, no stack trace to callers | Central log storage and tamper evidence are deferred |
| Denial of service | Local API unavailable | Bounded validation and container resource isolation boundary | Add resource limits, timeouts, rate limiting, and load tests before shared use |

## Abuse cases

- A caller supplies `restart_service` as an action type: domain validation rejects it.
- A caller supplies `read_only=false`: domain validation rejects it.
- A caller sends an unknown signal: the analyzer returns low confidence and requests more evidence.
- A caller injects a malformed correlation ID: middleware replaces it with a generated safe identifier.
- A contributor commits a token: local/CI secret scanners block the change and the token must be rotated.
- A dependency introduces a fixable critical CVE: dependency or container scanning blocks the pull request.

## Assumptions

- All incidents, identifiers, and evidence are synthetic.
- The service binds to loopback for direct local development.
- The Docker runtime and contributor host are maintained and trusted.
- GitHub branch protection is configured by the repository owner to require the CI checks.

## Review triggers

Review and update this model before adding authentication, persistent storage, external network collectors, AWS or Kubernetes credentials, AI providers, multi-tenancy, public exposure, policy/approval services, or any execution capability.
