"""Context management for request-scoped logging metadata."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_session_id() -> str | None:
    """Return the current session identifier, if any."""

    return _session_id_var.get()


def set_session_id(value: str | None) -> Any:
    """Bind a session identifier to the current context and return its token."""

    return _session_id_var.set(value)


def reset_session_id(token: Any) -> None:
    """Restore the previous session identifier using the provided token."""

    if token is not None:
        _session_id_var.reset(token)


def get_request_id() -> str | None:
    """Return the current request identifier, if any."""

    return _request_id_var.get()


def set_request_id(value: str | None) -> Any:
    """Bind a request identifier to the current context and return its token."""

    return _request_id_var.set(value)


def reset_request_id(token: Any) -> None:
    """Restore the previous request identifier using the provided token."""

    if token is not None:
        _request_id_var.reset(token)


def clear_context() -> None:
    """Clear any stored context values for the current execution flow."""

    _session_id_var.set(None)
    _request_id_var.set(None)


__all__ = [
    "get_session_id",
    "set_session_id",
    "reset_session_id",
    "get_request_id",
    "set_request_id",
    "reset_request_id",
    "clear_context",
]
