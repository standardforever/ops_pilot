# Local Development Runbook

## Purpose

Use this runbook to prepare, verify, start, inspect, stop, and troubleshoot the local OpsPilot service. All examples operate on synthetic data and require no cloud or AI-provider credentials.

## Prerequisites

- Git
- Docker Engine and Docker Compose v2
- `make`
- Python 3.12+ and `uv` for direct Python development

Confirm the tools:

```bash
git --version
docker --version
docker compose version
make --version
python3 --version
uv --version
```

## Bootstrap

```bash
git clone https://github.com/standardforever/ops_pilot.git
cd ops_pilot
make bootstrap
```

`make bootstrap` creates `.venv` and installs the exact dependency set in `uv.lock`.

## Verify before starting

```bash
make verify
```

The command fails if formatting, linting, typing, tests, 85% coverage, source analysis, dependency audit, or tracked-file secret scanning fails.

## Start with Docker Compose

```bash
make up
docker compose ps
make smoke
```

Expected state: the `ops-pilot` service is `healthy`, and the smoke command ends with `OpsPilot smoke test passed`.

The service binds only to `127.0.0.1:8000`. Check endpoints directly:

```bash
curl --fail http://127.0.0.1:8000/health/live
curl --fail http://127.0.0.1:8000/health/ready
```

## Run the complete demo

```bash
make demo
```

The demo verifies liveness, readiness, a supported high-CPU incident, an unknown incident, correlation/audit identifiers, read-only action metadata, and rejection of an invalid request.

## Inspect logs and audit output

```bash
docker compose logs ops-pilot
docker compose logs ops-pilot | grep 'analysis.completed'
docker compose logs ops-pilot | grep 'demo-correlation-id'
```

Each container log line is JSON. Request and audit events can be joined with `correlation_id`. Complete incident payloads and configured sensitive fields must not appear.

## Stop

```bash
make down
```

Compose sends `SIGTERM`, waits for the configured grace period, removes the container, and removes the project network. The image and local Python environment remain cached.

## Direct Python development

Start the reload server:

```bash
make run
```

In another terminal:

```bash
make smoke
make demo
```

Stop the direct server with `Ctrl+C`.

## Reset generated state

Stop containers first, then remove reproducible local output:

```bash
make down
make clean
```

To recreate dependencies without deleting source or configuration:

```bash
uv sync --frozen --group dev --refresh
```

## Common failures

### Port 8000 is already in use

Identify the existing listener or run the direct server on another loopback port:

```bash
PORT=8001 make run
HOST=127.0.0.1 PORT=8001 make smoke
```

Compose intentionally uses port 8000; stop the conflicting process before `make up`.

### Container is unhealthy

```bash
docker compose ps
docker compose logs ops-pilot
docker inspect ops_pilot-ops-pilot-1 --format '{{json .State.Health}}'
```

Rebuild from the locked inputs:

```bash
make down
docker compose build --no-cache
make up
```

### Dependency environment differs from the lockfile

```bash
uv sync --frozen --group dev
```

Do not hand-edit `uv.lock`. Update dependencies through `uv lock` in a dedicated pull request and rerun `make verify`.

### Security scan reports a finding

Do not bypass the check. Follow the [security baseline](../security/security-baseline.md) for triage, remediation, and time-limited exception requirements.

## Safety checks

- Never add cloud credentials or real incident data to `.env`, fixtures, commands, or logs.
- Do not expose the local port beyond loopback.
- Treat action proposals as investigation data, not authorization.
- Stop and report unexpected network access, command execution, or filesystem mutation.
