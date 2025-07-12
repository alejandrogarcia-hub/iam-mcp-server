# src/mcp_server_iam/__main__.py
from mcp_server_iam.config import settings
from mcp_server_iam.server import mcp


def main():
    mcp.run(transport=settings.transport)  # starts stdio server; blocks until exit


if __name__ == "__main__":
    main()
