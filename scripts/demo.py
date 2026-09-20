#!/usr/bin/env python3
"""Run the reproducible local OpsPilot demonstration."""

import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

CORRELATION_ID = "demo-correlation-id"


def request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    expected_status: int = 200,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "X-Correlation-ID": CORRELATION_ID},
        method="GET" if data is None else "POST",
    )
    try:
        with urlopen(request, timeout=5) as response:  # nosec B310 -- URL is loopback-validated
            assert response.status == expected_status
            result: dict[str, Any] = json.load(response)
            return result
    except HTTPError as error:
        if error.code != expected_status:
            raise
        result = json.load(error)
        return result


def display(title: str, payload: dict[str, Any]) -> None:
    print(f"\n## {title}")
    print(json.dumps(payload, indent=2, sort_keys=True))


def incident(signal_type: str, incident_id: str) -> dict[str, Any]:
    evidence = []
    if signal_type == "high_cpu":
        evidence = [
            {
                "evidence_id": "ev-demo-cpu",
                "kind": "metric",
                "name": "cpu_utilization_percent",
                "value": 96.4,
                "unit": "percent",
                "observed_at": "2026-09-20T11:59:00Z",
                "source": "synthetic-demo",
            }
        ]
    return {
        "schema_version": "1.0",
        "incident_id": incident_id,
        "occurred_at": "2026-09-20T12:00:00Z",
        "source": "synthetic-demo",
        "severity": "high",
        "signal_type": signal_type,
        "resource": "service:demo",
        "summary": "Synthetic incident used by the documented demonstration",
        "evidence": evidence,
    }


def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme != "http" or parsed_url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("the demo only permits an HTTP loopback address")

    live = request_json(f"{base_url}/health/live")
    ready = request_json(f"{base_url}/health/ready")
    supported = request_json(
        f"{base_url}/v1/incidents/analyze",
        payload=incident("high_cpu", "inc-demo-supported"),
    )
    unknown = request_json(
        f"{base_url}/v1/incidents/analyze",
        payload=incident("unknown", "inc-demo-unknown"),
    )
    invalid_payload = incident("high_cpu", "inc-demo-invalid")
    invalid_payload.pop("incident_id")
    invalid = request_json(
        f"{base_url}/v1/incidents/analyze",
        payload=invalid_payload,
        expected_status=422,
    )

    assert live["status"] == ready["status"] == "ok"
    assert supported["confidence"] >= 0.8
    assert supported["recommendations"][0]["action"]["read_only"] is True
    assert supported["correlation_id"] == CORRELATION_ID
    assert supported["audit_event_id"].startswith("audit-")
    assert unknown["confidence"] <= 0.2
    assert invalid["error_code"] == "invalid_request"

    display("Liveness", live)
    display("Readiness", ready)
    display("Supported incident", supported)
    display("Unknown incident", unknown)
    display("Rejected invalid incident", invalid)
    print("\nOpsPilot demonstration passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
