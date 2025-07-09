# src/mcp_server_iam/__main__.py
from config import settings
from server import mcp


if __name__ == "__main__":
    # Optionally parse CLI flags here before launch
    mcp.run(transport=settings.transport)  # starts stdio server; blocks until exit
