# Contributing to OpsPilot

Thank you for helping build OpsPilot. Contributions should be small, traceable, tested, and safe by default.

## Before starting

1. Read the [architecture overview](docs/architecture/overview.md) and applicable ADRs.
2. Choose an open issue whose dependencies are complete.
3. Ask for clarification on the issue before coding when scope or acceptance criteria are ambiguous.
4. Never include credentials, production identifiers, private endpoints, or customer data.

## Development setup

OpsPilot supports Python 3.12 or later. Once the application scaffold is present, the standard workflow is:

```bash
make bootstrap
make verify
```

Use the commands in the root `Makefile` rather than inventing a second local workflow. See the local-development runbook for operating instructions.

## Branching

Create a branch from the latest `main` using one of these prefixes:

- `feat/` for product behavior
- `fix/` for defect corrections
- `docs/` for documentation only
- `chore/` for maintenance, tooling, or governance
- `security/` for security controls

Include the issue number where practical, for example `feat/7-incident-analysis`.

Do not commit directly to `main`. Keep one logical issue per branch and avoid unrelated refactoring.

## Commit messages

Use Conventional Commit-style messages:

```text
<type>(<optional scope>): <imperative summary>
```

Accepted types are `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`, `security`, and `revert`.

Examples:

```text
feat(api): add readiness endpoint
test(analysis): cover unknown incident fallback
security(container): run service as non-root
```

Use the body to explain why a change is necessary, important trade-offs, and migration or rollback information. Reference the issue in the pull request rather than relying only on a commit message.

## Verification

Run the complete local gate before opening or updating a pull request:

```bash
make verify
```

When the change affects the runtime image, also run:

```bash
docker compose up --build -d
make smoke
docker compose down
```

Tests must be deterministic and must not require cloud credentials, an AI-provider key, or internet access. Add tests for success, boundary, failure, and fail-closed behavior where applicable.

## Pull requests

Every pull request must:

- Link its issue with `Closes #<number>` only when all acceptance criteria are met.
- Explain the behavior and reason for the change.
- List validation commands and their results.
- Describe security, privacy, operational, and rollback impact.
- Update documentation when commands, interfaces, architecture, or user-visible behavior change.
- Remain focused enough to review and revert safely.

Do not merge with failing checks. Prefer a normal merge when preserving meaningful individual commits; use squash only when the branch history has no independent value.

## CI dependency policy

GitHub Actions are pinned to complete commit SHAs and include the corresponding release tag in a comment. When updating an action:

1. Read the upstream release notes and identify breaking or permission changes.
2. Verify the release tag and resolve it to its immutable commit SHA.
3. Update both the SHA and version comment in the same pull request.
4. Confirm workflow permissions remain read-only unless a documented step requires more.
5. Run the local verification gate and require the updated workflow to pass before merge.

Runtime and development dependencies are resolved in `uv.lock`; do not hand-edit that file.

## Review expectations

Reviewers check correctness, scope, tests, security boundaries, observability, failure behavior, documentation, and maintainability. Resolve discussions with code or an explicit documented decision.

## Reporting defects and vulnerabilities

Use the issue templates for ordinary defects and feature requests. Do not report suspected vulnerabilities publicly. Follow [SECURITY.md](SECURITY.md) for private reporting.
