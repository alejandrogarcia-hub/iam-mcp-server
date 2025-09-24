"""Application logging utilities with request-scoped context."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from pythonjsonlogger.json import JsonFormatter

from mcp_server_iam.context import get_request_id, get_session_id


class RequestContextFilter(logging.Filter):
    """Inject current session/request identifiers into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - concise docstring
        record.session_id = get_session_id() or "unknown"
        record.request_id = get_request_id() or "unknown"
        return True


def setup_logging(level: int, *, include: Iterable[str] | None = None) -> None:
    """Configure structured JSON logging for the application."""

    handler = logging.StreamHandler()
    handler.addFilter(RequestContextFilter())
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(session_id)s %(request_id)s",
        json_default=str,
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    logging.captureWarnings(True)

    if include:
        for logger_name in include:
            logging.getLogger(logger_name).setLevel(level)


__all__ = ["setup_logging", "RequestContextFilter"]
