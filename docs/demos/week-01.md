# Foundation and Safe Local Slice Demonstration

## What this proves

This demonstration proves that a clean OpsPilot checkout can run a hardened local API, analyze synthetic incidents deterministically, preserve uncertainty, reject invalid input, and correlate its response with structured audit output without infrastructure credentials or mutation.

## Prepare and verify

```bash
git clone https://github.com/standardforever/ops_pilot.git
cd ops_pilot
make bootstrap
make verify
make up
```

Expected evidence:

- All quality and security checks pass.
- Test coverage remains at or above 85%.
- Compose reports `ops-pilot` as healthy.
- No AWS credential or AI-provider key is requested.

## Execute

```bash
make demo
```

The script stops with a non-zero status if any assertion fails. On success it prints five JSON sections and ends with:

```text
OpsPilot demonstration passed.
```

## Evidence to inspect

### Liveness and readiness

Both responses have HTTP 200 and include:

```json
{
  "schema_version": "1.0",
  "service": "ops-pilot",
  "status": "ok",
  "version": "0.1.0"
}
```

### Supported incident

The high-CPU result has confidence of at least `0.8`, cites `ev-demo-cpu`, returns an `audit-*` identifier, preserves `demo-correlation-id`, and contains only a read-only action:

```json
{
  "action_type": "inspect_metrics",
  "read_only": true,
  "requires_approval": false,
  "risk_level": "informational"
}
```

### Unknown incident

The unknown result has confidence at or below `0.2`, explicitly states its limitations, and recommends collecting more evidence rather than inventing a cause.

### Invalid incident

The request without `incident_id` returns HTTP 422 with `error_code` set to `invalid_request`, a correlation ID, and no stack trace or input echo.

### Audit correlation

```bash
docker compose logs ops-pilot | grep 'analysis.completed'
docker compose logs ops-pilot | grep 'demo-correlation-id'
```

The `analysis.completed` event identifier matches the response's `audit_event_id`; the request and audit event share `correlation_id`.

## Stop and clean up

```bash
make down
```

## Deliberate limitations

The demonstration does not execute commands, connect to AWS or Kubernetes, use Terraform or Ansible, contact an AI provider, persist incident data, authenticate users, or remediate infrastructure. Those capabilities require later architecture, policy, security, and verification stages.

The planned delivery order is AWS/Terraform, then Kubernetes/Helm, followed by Prometheus/Grafana and Argo CD. Security controls evolve continuously across those stages.
