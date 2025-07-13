from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# Load variables declared in a `.env` file into the process environment
load_dotenv()


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""

    pass


class AppConfig(BaseSettings):
    """Application configuration sourced from environment variables.

    The class automatically reads variables from the OS environment as soon as
    an instance is created. We call :pyfunc:`dotenv.load_dotenv` at import time
    so that both shell variables *and* the local ``.env`` file are considered.

    Attributes
    ----------
    app_env: str
        Logical environment name (e.g., *development*, *staging*, *production*).
    debug: bool
        Flag that toggles debug mode across the application.
    log_level: str
        Root logging level for the application.
    app_name: str
        Name of the application.
    rapidapi_key: str
        API key for interacting with RapidAPI services.
    rapidapi_host: str
        Host for interacting with RapidAPI services.

    """

    app_name: str = Field(
        default="iam",
        alias="APP_NAME",
        description="Application name used for logging and identification",
        min_length=1,
        max_length=50,
    )

    log_level: int = Field(
        default=logging.INFO,
        description="Logging level, default info",
        alias="LOG_LEVEL",
        ge=logging.DEBUG,
        le=logging.CRITICAL,
    )

    transport: str = Field(
        default="stdio",
        description="Transport for MCP server",
        alias="MCP_TRANSPORT",
        examples=["stdio", "sse", "mcp_remote"],
    )

    resume_mesh_filename: str = Field(
        default="resume_mesh",
        alias="RESUME_MESH_FILENAME",
        description="Default filename for resume mesh",
        pattern=r"^[a-zA-Z0-9_\-]+$",
    )

    rapidapi_key: str | None = Field(
        default="",
        alias="RAPIDAPI_KEY",
        description="RapidAPI key for external API access",
    )

    rapidapi_host: str | None = Field(
        default="jsearch.p.rapidapi.com",
        alias="RAPIDAPI_HOST",
        description="RapidAPI host endpoint",
        pattern=r"^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$",
    )

    @field_validator("app_name", mode="before")
    @classmethod
    def validate_app_name(cls, v: str) -> str:
        """Validate and clean app name."""
        if not v or not v.strip():
            raise ValueError("App name cannot be empty")

        # Remove special characters and convert to lowercase
        cleaned = "".join(c for c in v.strip().lower() if c.isalnum() or c in "_-")
        if not cleaned:
            raise ValueError(
                "App name must contain at least one alphanumeric character"
            )

        return cleaned

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        """Convert string log levels to integers."""
        if isinstance(v, str):
            level_name = v.upper().strip()
            if level_name in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
                return getattr(logging, level_name)
            try:
                level_int = int(v)
                if logging.DEBUG <= level_int <= logging.CRITICAL:
                    return level_int
                else:
                    raise ValueError(f"Log level {level_int} is outside valid range")
            except ValueError:
                raise ValueError(f"Invalid log level: {v}")

        if isinstance(v, int):
            if logging.DEBUG <= v <= logging.CRITICAL:
                return v
            else:
                raise ValueError(f"Log level {v} is outside valid range")

        return logging.INFO

    @field_validator("resume_mesh_filename", mode="after")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename format."""
        # Check for invalid characters
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Filename contains invalid characters: {invalid_chars}")

        return v

    @property
    def resumes_dir(self) -> str:
        """Return the path to the resumes directory."""
        # Build an absolute path to ``src/resources/resumes`` regardless of
        # the current working directory. We derive the location from this file
        # (``src/config.py``), then navigate into the package resources folder.

        base_path = Path(__file__).resolve().parent  # -> src/
        resumes_path = (base_path / "resources" / "resumes").resolve()

        # Ensure the directory exists
        try:
            resumes_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigurationError(f"Failed to create resumes directory: {e}") from e

        return str(resumes_path)

    @property
    def log_level_name(self) -> str:
        """Return the log level as a string name."""
        return logging.getLevelName(self.log_level)

    model_config = ConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


# ============================
# Module-level helper
# ============================


@lru_cache(maxsize=1)
def get_settings() -> AppConfig:
    """Return a *cached* ``AppConfig`` instance.

    Using :pyfunc:`functools.lru_cache` guarantees that environment validation
    happens only once per interpreter session, while subsequent calls share the
    same object—this is our *dependency-injection* ready entry-point.

    Returns
    -------
    AppConfig
        A validated settings object populated from the environment.

    Raises
    ------
    ConfigurationError
        If configuration validation fails.
    """

    try:
        return AppConfig()
    except Exception as exc:
        raise ConfigurationError(f"Configuration setup failed: {exc}") from exc


# Create a global instance of the configuration
settings = get_settings()
