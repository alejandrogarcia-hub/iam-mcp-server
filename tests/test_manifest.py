"""Regression tests for manifest metadata."""

import json
from pathlib import Path


def test_manifest_prompts_are_runtime_described():
    """Manifest prompt text should not contain hard-coded sample personas."""

    manifest = json.loads(Path("manifest.json").read_text())

    prompt_texts = [entry.get("text", "") for entry in manifest.get("prompts", [])]

    assert all("Generated at runtime" in text for text in prompt_texts)
    assert all("AI Engineer" not in text for text in prompt_texts)
