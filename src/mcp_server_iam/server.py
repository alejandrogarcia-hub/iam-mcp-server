from mcp.server.fastmcp import FastMCP

from config import settings

mcp = FastMCP(
    name=settings.app_name,
    version=settings.app_version,
    log_level=settings.log_level_name,
)
