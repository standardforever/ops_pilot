"""Validated application configuration."""

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported runtime environments."""

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Settings loaded only from explicit values and OPSPILOT_* variables."""

    model_config = SettingsConfigDict(
        env_prefix="OPSPILOT_",
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="ops-pilot", min_length=1, max_length=64)
    environment: Environment = Environment.LOCAL
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    docs_enabled: bool = True
    host: str = Field(default="127.0.0.1", min_length=1, max_length=255)
    port: int = Field(default=8000, ge=1, le=65535)
