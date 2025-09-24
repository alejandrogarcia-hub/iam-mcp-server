# syntax=docker/dockerfile:1.7-labs

ARG PYTHON_VERSION="3.11"
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential curl \
    && rm -rf /var/lib/apt/lists/*

ARG APP_VERSION=local

COPY pyproject.toml requirements.txt uv.lock ./
COPY src ./src

RUN pip install --upgrade pip setuptools wheel \
    && if [ "${APP_VERSION}" = "local" ]; then \
         if [ "${CI:-}" = "true" ]; then \
             echo "Error: APP_VERSION must be provided when building in CI" >&2; \
             exit 1; \
         fi; \
         pip install --no-cache-dir -r requirements.txt; \
       else \
         WHEEL_PATH=$(ls dist/iam_mcp_server-${APP_VERSION}-*.whl 2>/dev/null || true); \
         if [ -n "$WHEEL_PATH" ]; then \
             pip install --no-cache-dir "$WHEEL_PATH"; \
         else \
             pip install --no-cache-dir "iam-mcp-server==${APP_VERSION}"; \
         fi; \
       fi \
    && PYTHONPATH=/app/src python -c "import mcp_server_iam; print('MCP server module loaded successfully')"

RUN useradd --create-home --home /home/iam iam \
    && mkdir -p /data \
    && chown -R iam:iam /data

USER iam

ENV IAM_DATA_ROOT=/data \
    LOG_LEVEL=INFO \
    MCP_TRANSPORT=stdio \
    PORT=8080 \
    HOST=0.0.0.0

VOLUME ["/data"]

# Expose port for HTTP mode
EXPOSE 8080

ENV PYTHONPATH=/app/src${PYTHONPATH:+:$PYTHONPATH}

# Default to stdio mode, but allow override via CMD
ENTRYPOINT ["python", "-m"]
CMD ["mcp_server_iam"]
