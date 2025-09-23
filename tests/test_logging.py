"""Tests for structured logging configuration."""

import logging

from mcp_server_iam.logging import setup_logging


def test_setup_logging_configures_root_handler():
    root = logging.getLogger()
    original_handlers = list(root.handlers)

    for handler in original_handlers:
        root.removeHandler(handler)

    try:
        setup_logging(logging.INFO)
        assert root.level == logging.INFO
        assert len(root.handlers) == 1
    finally:
        root.handlers.clear()
        for handler in original_handlers:
            root.addHandler(handler)
