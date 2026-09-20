# Week 1 Security Baseline

## Purpose and scope

This baseline defines the minimum controls for source code, dependencies, secrets, container images, runtime configuration, logs, and vulnerability response. It applies to every pull request and the default branch.

OpsPilot is pre-alpha, local-only, and read-only. These controls do not make it production-ready and do not authorize use of production credentials or data.

## Enforced controls

| Concern | Control | Local evidence | CI evidence |
|---|---|---|---|
| Source vulnerabilities | Bandit scans `src/` using repository configuration | `make security` | `make verify` quality job |
| Dependency vulnerabilities | `pip-audit` evaluates the locked environment | `make security` | `make verify` quality job |
| Committed secrets | detect-secrets checks tracked files against a reviewed baseline | `make secrets` | `make verify` quality job |
| Git-history secrets | Gitleaks scans complete pull-request history using `.gitleaks.toml` | `gitleaks detect --config .gitleaks.toml` | Secret-scan job |
| Container vulnerabilities | Trivy scans OS and library packages | `trivy image --severity HIGH,CRITICAL --ignore-unfixed ops-pilot:local` | Container job |
| Runtime privilege | Fixed non-root UID, all Linux capabilities dropped, no-new-privileges, read-only root filesystem | `docker compose up --build` and inspection | Container job |
| Dependency drift | `uv.lock`, pinned build tools, immutable action SHAs | `uv sync --frozen` | Quality and container jobs |
| Dependency updates | Dependabot covers uv, Docker, and GitHub Actions | Pull-request review | Weekly update checks |
| Sensitive logging | Central recursive redaction and metadata-only audit events | Automated tests | Quality job |

## Blocking policy

A pull request must not merge when any of the following is present:

- A detected credential, token, private key, or unreviewed secret-like value
- A known fixable high or critical vulnerability in the built image
- A known vulnerable direct dependency without an approved exception
- A Bandit finding at medium or higher confidence and severity that is not proven false
- Failure of the read-only domain invariant or non-root container check
- An unpinned GitHub Action reference

The security gate fails closed. Scanner outages or ambiguous results require investigation; they are not treated as successful checks.

## Severity and remediation targets

| Severity | Response target | Remediation target |
|---|---:|---:|
| Critical | Same business day | Before merge; within 72 hours on `main` |
| High | Two business days | Before merge; within 7 days on `main` |
| Medium | Five business days | Within 30 days |
| Low | Next planning review | Risk-based |

Because the project is pre-alpha, disabling an affected feature or reverting a dependency is preferred over accepting critical risk.

## Exceptions and false positives

Scanner suppression must be narrow and documented next to the affected rule when the tool supports it. Every temporary exception requires:

- A GitHub issue and accountable owner
- The scanner, rule, package, version, and affected component
- Evidence explaining why the finding is false positive or temporarily unavoidable
- Compensating controls
- An expiry date no later than 30 days for high/critical findings
- A removal or remediation plan

Broad directory exclusions and permanent high/critical allowlists are prohibited. Baseline files are reviewed artifacts, not places to hide unexplained findings.

## Secret response

If a real secret is committed:

1. Revoke or rotate it immediately; deleting the Git commit is not sufficient.
2. Identify access and use through the owning provider's audit records.
3. Remove the value from the repository and history where appropriate.
4. Record the incident privately, including exposure window and affected permissions.
5. Add a safe regression fixture or detection rule without preserving the secret.

Suspected vulnerabilities are reported privately according to [SECURITY.md](../../SECURITY.md).

## Release boundary

Week 1 uses synthetic data, no cloud SDK, no infrastructure credentials, no arbitrary commands, and no mutating action type. Introducing AWS, Kubernetes, external AI, authentication, persistent storage, or an executor requires an updated threat model and additional controls before merge.
