"""Tests for application configuration utilities."""

from pathlib import Path

import pytest

from mcp_server_iam import config


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Ensure settings cache is cleared between tests."""
    config.get_settings.cache_clear()
    try:
        yield
    finally:
        config.get_settings.cache_clear()


def test_resumes_dir_uses_configured_data_root(monkeypatch, tmp_path):
    """Configured IAM_DATA_ROOT should control the resume storage location."""

    monkeypatch.setenv("IAM_DATA_ROOT", str(tmp_path))

    settings = config.get_settings()
    resumes_path = Path(settings.resumes_dir)

    assert resumes_path.is_dir()
    assert resumes_path.parent == tmp_path.resolve()


def test_resumes_dir_defaults_to_xdg_data_home(monkeypatch, tmp_path):
    """When IAM_DATA_ROOT is unset, fall back to XDG_DATA_HOME."""

    monkeypatch.delenv("IAM_DATA_ROOT", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    settings = config.get_settings()
    expected_root = (tmp_path / "iam-mcp-server").resolve()
    expected = expected_root / "resumes"

    resumes_path = Path(settings.resumes_dir)

    assert resumes_path == expected
    assert resumes_path.is_dir()
