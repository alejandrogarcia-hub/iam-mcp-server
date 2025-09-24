"""Tests for request-scoped context utilities."""

from mcp_server_iam import context


def test_session_context_round_trip():
    token = context.set_session_id("session-123")
    assert context.get_session_id() == "session-123"
    context.reset_session_id(token)
    assert context.get_session_id() is None


def test_request_context_round_trip():
    token = context.set_request_id("req-456")
    assert context.get_request_id() == "req-456"
    context.reset_request_id(token)
    assert context.get_request_id() is None


def test_clear_context():
    context.set_session_id("abc")
    context.set_request_id("def")
    context.clear_context()
    assert context.get_session_id() is None
    assert context.get_request_id() is None
