"""Unit tests for utility helpers."""

from mcp_server_iam.utils import sanitize_text


def test_sanitize_text_escapes_html():
    result = sanitize_text("<div>alert('hi')</div>")
    assert result == "&lt;div&gt;alert(&#x27;hi&#x27;)&lt;/div&gt;"


def test_sanitize_text_truncates_when_limit_exceeded():
    text = "abcdef"
    result = sanitize_text(text, limit=3)
    assert result == "abc\n...\n"
