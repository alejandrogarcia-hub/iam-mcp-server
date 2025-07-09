from mcp.server.fastmcp import FastMCP

from mcp_server_iam.config import settings

mcp = FastMCP(
    name=settings.app_name,
    version=settings.app_version,
    log_level=settings.log_level_name,
)
