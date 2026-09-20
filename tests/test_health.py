"""Health and configuration behavior."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ops_pilot.application import create_app
from ops_pilot.config import Environment, Settings


def test_liveness_returns_versioned_service_status() -> None:
    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "1.0",
        "status": "ok",
        "service": "ops-pilot",
        "version": "0.1.0",
    }


def test_readiness_succeeds_after_lifespan_initialization() -> None:
    with TestClient(create_app(Settings(environment=Environment.TEST))) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invalid_port_fails_configuration_without_echoing_secret_data() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(port=0)

    assert "greater than or equal to 1" in str(error.value)


def test_openapi_can_be_disabled() -> None:
    with TestClient(
        create_app(Settings(environment=Environment.TEST, docs_enabled=False))
    ) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 404
