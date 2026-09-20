"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ops_pilot import __version__
from ops_pilot.api.errors import ErrorResponse, ValidationProblem
from ops_pilot.api.health import router as health_router
from ops_pilot.api.incidents import router as incidents_router
from ops_pilot.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct the API without starting a server or performing external I/O."""

    resolved_settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.ready = True
        try:
            yield
        finally:
            app.state.ready = False

    app = FastAPI(
        title="OpsPilot API",
        summary="Safe, deterministic infrastructure incident analysis",
        version=__version__,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        openapi_url="/openapi.json" if resolved_settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.ready = False
    app.include_router(health_router)
    app.include_router(incidents_router)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        details = tuple(
            ValidationProblem(
                location=tuple(error["loc"]),
                message=error["msg"],
                problem_type=error["type"],
            )
            for error in exception.errors()
        )
        payload = ErrorResponse(
            error_code="invalid_request",
            message="The request does not satisfy the incident contract.",
            details=details,
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    return app
