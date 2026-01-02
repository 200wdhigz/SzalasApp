# Multi-stage build for production-ready Flask app with Poetry
# Stage 1: Builder - Install dependencies using Poetry
FROM python:3.12-slim AS builder

# Install Poetry
ENV POETRY_VERSION=2.2.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY app/pyproject.toml app/poetry.lock app/poetry.toml ./

# Install dependencies (production only)
RUN poetry install --only main,prod --no-root --no-ansi && \
    rm -rf ${POETRY_CACHE_DIR}

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code from app/ directory
COPY --chown=appuser:appuser app/ /app/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Health check endpoint (assumes /health or similar exists)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health', timeout=5)" || exit 1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Run with Gunicorn for production
CMD gunicorn --bind 0.0.0.0:${PORT} \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    app:app
