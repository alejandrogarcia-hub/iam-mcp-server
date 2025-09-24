"""HTTP/SSE transport wrapper for MCP server."""

import logging
import os
import uuid
from functools import wraps

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_server_iam.config import settings
from mcp_server_iam.context import set_request_id, set_session_id
from mcp_server_iam.logging import RequestContextFilter, setup_logging
from mcp_server_iam.server import mcp


def patch_mcp_server():
    """Patch MCP server to propagate context from request metadata."""
    # Get the MCP server logger and add our filter
    mcp_logger = logging.getLogger("mcp.server.lowlevel.server")
    if not any(isinstance(f, RequestContextFilter) for f in mcp_logger.filters):
        mcp_logger.addFilter(RequestContextFilter())

    # Store reference to original _handle_request method
    original_handle_request = mcp._mcp_server._handle_request

    @wraps(original_handle_request)
    async def patched_handle_request(
        message, req, session, lifespan_context, raise_exceptions
    ):
        """Wrapper that extracts and sets context from message metadata."""
        # Extract request context from message metadata if available
        if hasattr(message, "message_metadata") and message.message_metadata:
            metadata = message.message_metadata
            if hasattr(metadata, "request_context"):
                request = metadata.request_context
                if hasattr(request, "query_params"):
                    # Extract session_id from query params
                    session_id = request.query_params.get("session_id")
                    if session_id:
                        set_session_id(session_id)

                    # Generate or extract request_id
                    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
                    set_request_id(request_id)

        # Call original method with correct arguments (5 args, not 6)
        return await original_handle_request(
            message, req, session, lifespan_context, raise_exceptions
        )

    # Apply the patch
    mcp._mcp_server._handle_request = patched_handle_request


def create_app():
    """Create Starlette app with SSE transport."""
    setup_logging(settings.log_level, include=["mcp"])

    # Patch MCP server to properly propagate context
    patch_mcp_server()

    # Get the Starlette app from FastMCP with SSE support
    # This creates an app with /sse endpoint for SSE and /messages for HTTP POST
    app = mcp.sse_app()

    class LoggingContextMiddleware(BaseHTTPMiddleware):
        """Attach request and session identifiers to logging context for middleware-level operations."""

        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
            session_id = request.query_params.get("session_id") or request.headers.get(
                "x-session-id"
            )
            request_id = uuid.uuid4().hex

            # Set context variables for middleware-level logging
            if session_id:
                set_session_id(session_id)
            set_request_id(request_id)

            response = await call_next(request)

            # Surface identifiers in response headers for easier tracing
            if session_id:
                response.headers.setdefault("X-Session-ID", session_id)
            response.headers.setdefault("X-Request-ID", request_id)

            return response

    app.add_middleware(LoggingContextMiddleware)

    # Add health check endpoint using Starlette's add_route
    async def health_check(request):
        """Health check endpoint for Kubernetes probes."""
        return JSONResponse({"status": "healthy", "service": "iam-mcp-server"})

    app.add_route("/health", health_check, methods=["GET"])

    # Configure CORS if origins are specified
    cors_origins = os.getenv("CORS_ORIGINS", "").strip()
    if cors_origins:
        # Parse comma-separated origins or use wildcard
        allowed_origins = (
            ["*"]
            if cors_origins == "*"
            else [
                origin.strip() for origin in cors_origins.split(",") if origin.strip()
            ]
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Session-ID"],
        )

    return app


def main():
    """Run HTTP/SSE server."""
    app = create_app()
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=settings.log_level_name.lower(),
    )


if __name__ == "__main__":
    main()
