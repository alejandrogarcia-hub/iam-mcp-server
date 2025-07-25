"""Individual Applicant Mesh (IAM) MCP Server.

A Model Context Protocol server for job search automation and analysis.
"""

import sys

try:
    from importlib.metadata import version

    __version__ = version("iam-mcp-server")  # matches project.name in pyproject.toml
except Exception:
    # Fallback for development environments or if package not installed
    __version__ = "unknown"

__all__ = ["__version__"]
