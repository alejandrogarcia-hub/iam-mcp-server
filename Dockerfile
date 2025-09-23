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

COPY pyproject.toml README.md requirements.txt requirements-dev.txt uv.lock ./
COPY src ./src

RUN pip install --upgrade pip setuptools wheel \
    && if [ "${APP_VERSION}" = "local" ]; then \
         pip install --no-cache-dir -r requirements.txt; \
       else \
         pip install --no-cache-dir "iam-mcp-server==${APP_VERSION}"; \
       fi \
    && PYTHONPATH=/app/src python -c "import mcp_server_iam; print('MCP server module loaded successfully')"

RUN useradd --create-home --home /home/iam iam \
    && mkdir -p /data \
    && chown -R iam:iam /data

USER iam

ENV IAM_DATA_ROOT=/data \
    LOG_LEVEL=INFO \
    MCP_TRANSPORT=stdio

VOLUME ["/data"]

ENV PYTHONPATH=/app/src${PYTHONPATH:+:$PYTHONPATH}

ENTRYPOINT ["python", "-m", "mcp_server_iam"]
