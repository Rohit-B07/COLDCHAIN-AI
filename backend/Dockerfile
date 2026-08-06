# syntax=docker/dockerfile:1

# ---- Stage 1: build wheels (dependency resolution & caching) -----------------
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /wheels

COPY pyproject.toml ./
COPY app ./app

RUN pip wheel --wheel-dir /wheels/dist -e .

# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security hardening.
RUN groupadd -r coldchain && useradd -r -g coldchain -m coldchain

WORKDIR /app

COPY --from=builder /wheels/dist /wheels/dist
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir /wheels/dist/*.whl

COPY --chown=coldchain:coldchain alembic.ini ./
COPY --chown=coldchain:coldchain migrations ./migrations
COPY --chown=coldchain:coldchain app ./app

USER coldchain

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://localhost:8000/api/v1/health >/dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
