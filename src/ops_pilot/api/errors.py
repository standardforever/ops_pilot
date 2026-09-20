"""Stable, safe API error contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationProblem(BaseModel):
    """One sanitized request validation problem."""

    model_config = ConfigDict(extra="forbid")

    location: tuple[str | int, ...]
    message: str
    problem_type: str


class ErrorResponse(BaseModel):
    """Versioned error response that excludes stack traces and input values."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    error_code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Safe summary for the caller")
    details: tuple[ValidationProblem, ...] = ()
