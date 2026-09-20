"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from ops_pilot import __version__

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Versioned health endpoint response."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = Field(
        default="1.0", description="Health response contract version"
    )
    status: Literal["ok"] = Field(description="Component health status")
    service: str = Field(description="Service identifier")
    version: str = Field(description="Application version")


@router.get("/live", response_model=HealthResponse, summary="Process liveness")
async def liveness(request: Request) -> HealthResponse:
    """Report that the HTTP process can answer requests."""

    return HealthResponse(
        status="ok",
        service=request.app.state.settings.service_name,
        version=__version__,
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={503: {"description": "Application initialization is incomplete"}},
    summary="Application readiness",
)
async def readiness(request: Request, response: Response) -> HealthResponse:
    """Report whether required local application components are initialized."""

    if not request.app.state.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok",
        service=request.app.state.settings.service_name,
        version=__version__,
    )
