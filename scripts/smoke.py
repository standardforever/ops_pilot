#!/usr/bin/env python3
"""Dependency-free smoke test for an already running OpsPilot service."""

import json
import sys
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def request_json(url: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send one bounded local request and decode its JSON object response."""

    data = None if payload is None else json.dumps(payload).encode()
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "X-Correlation-ID": "smoke-test"},
        method="GET" if data is None else "POST",
    )
    with urlopen(request, timeout=5) as response:  # nosec B310 -- URL is loopback-validated
        result: dict[str, Any] = json.load(response)
        return result


def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme != "http" or parsed_url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("the smoke test only permits an HTTP loopback address")
    live = request_json(f"{base_url}/health/live")
    ready = request_json(f"{base_url}/health/ready")
    incident = {
        "schema_version": "1.0",
        "incident_id": "inc-smoke-001",
        "occurred_at": "2026-09-20T12:00:00Z",
        "source": "synthetic-smoke-test",
        "severity": "high",
        "signal_type": "high_cpu",
        "resource": "service:smoke-demo",
        "summary": "Synthetic CPU signal used by the container smoke test",
        "evidence": [
            {
                "evidence_id": "ev-smoke-cpu",
                "kind": "metric",
                "name": "cpu_utilization_percent",
                "value": 95.0,
                "unit": "percent",
                "observed_at": "2026-09-20T11:59:00Z",
                "source": "synthetic-smoke-test",
            }
        ],
    }
    plan = request_json(f"{base_url}/v1/incidents/analyze", payload=incident)

    assert live["status"] == "ok"
    assert ready["status"] == "ok"
    assert plan["incident_id"] == incident["incident_id"]
    assert plan["correlation_id"] == "smoke-test"
    assert plan["recommendations"][0]["action"]["read_only"] is True
    print(f"OpsPilot smoke test passed: {base_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
