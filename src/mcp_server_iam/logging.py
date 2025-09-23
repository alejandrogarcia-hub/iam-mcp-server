"""Application logging utilities."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from pythonjsonlogger.json import JsonFormatter


def setup_logging(level: int, *, include: Iterable[str] | None = None) -> None:
    """Configure structured JSON logging for the application."""

    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
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
