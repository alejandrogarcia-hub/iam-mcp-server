"""Tests for structured logging configuration."""

import logging

import pytest

from mcp_server_iam.context import (
    reset_request_id,
    reset_session_id,
    set_request_id,
    set_session_id,
)
from mcp_server_iam.logging import RequestContextFilter, setup_logging


@pytest.fixture()
def restore_root_logger():
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    for handler in original_handlers:
        root.removeHandler(handler)

    yield root

    root.handlers.clear()
    root.setLevel(original_level)
    for handler in original_handlers:
        root.addHandler(handler)


def test_setup_logging_attaches_context_filter(restore_root_logger, caplog, capfd):
    root = restore_root_logger

    setup_logging(logging.INFO)

    assert root.level == logging.INFO
    assert len(root.handlers) == 1

    handler = root.handlers[0]
    assert any(isinstance(flt, RequestContextFilter) for flt in handler.filters)

    session_token = set_session_id("session-xyz")
    request_token = set_request_id("req-123")

    logger = logging.getLogger(__name__)
    with caplog.at_level(logging.INFO):
        logger.info("structured test")

    reset_request_id(request_token)
    reset_session_id(session_token)

    stderr_output = capfd.readouterr().err
    assert '"session_id": "session-xyz"' in stderr_output
    assert '"request_id": "req-123"' in stderr_output
