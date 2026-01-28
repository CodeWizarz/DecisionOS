# Multi-stage build for optimized production images
# Stage 1: Builder
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install system deps for building wheels (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy dependency definition
COPY pyproject.toml poetry.lock* ./

# Install runtime dependencies (no dev deps)
RUN poetry install --only main --no-root

# Stage 2: Runtime
FROM python:3.11-slim-bookworm as runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime system libs (e.g. libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src /app/src
COPY alembic.ini /app/
# (Optional) COPY alembic /app/alembic

# Create a non-root user for security
RUN groupadd -g 1000 decisionos && \
    useradd -u 1000 -g decisionos -s /bin/bash -m decisionos && \
    chown -R decisionos:decisionos /app

USER decisionos

# Default to API, but can be overridden for worker
CMD ["uvicorn", "src.decisionos.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
