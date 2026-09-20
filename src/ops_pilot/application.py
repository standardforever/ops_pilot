"""FastAPI application factory."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ops_pilot import __version__
from ops_pilot.api.errors import ErrorResponse, ValidationProblem
from ops_pilot.api.health import router as health_router
from ops_pilot.api.incidents import router as incidents_router
from ops_pilot.config import Settings
from ops_pilot.observability import (
    CORRELATION_HEADER,
    AuditSink,
    LoggingAuditSink,
    normalize_correlation_id,
)
from ops_pilot.observability.logging import configure_logging


def create_app(
    settings: Settings | None = None,
    *,
    audit_sink: AuditSink | None = None,
) -> FastAPI:
    """Construct the API without starting a server or performing external I/O."""

    resolved_settings = settings or Settings()
    logger = configure_logging(resolved_settings)

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
    app.state.audit_sink = audit_sink or LoggingAuditSink(logger)
    app.state.ready = False
    app.include_router(health_router)
    app.include_router(incidents_router)

    @app.middleware("http")
    async def correlation_and_request_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = normalize_correlation_id(request.headers.get(CORRELATION_HEADER))
        request.state.correlation_id = correlation_id
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        finally:
            duration_ms = round((perf_counter() - started) * 1000, 3)
            logger.info(
                "request.completed",
                extra={
                    "correlation_id": correlation_id,
                    "route": request.url.path,
                    "method": request.method,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
        response.headers[CORRELATION_HEADER] = correlation_id
        return response

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exception: RequestValidationError
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
            correlation_id=request.state.correlation_id,
            details=details,
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    return app
