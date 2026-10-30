# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=0 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
COPY src/ /app/src/

# Install only production dependencies once
RUN uv sync --frozen --no-dev --no-editable \
    && find /app/.venv -type d \( -name "__pycache__" -o -name "tests" -o -name "test" \) -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true

# --- Stage 2: Minimal Production Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    CHURN_MODEL_PATH=/app/outputs/model.joblib

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/src /app/src
COPY --chown=appuser:appuser outputs/ /app/outputs/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "churn.api:app", "--host", "0.0.0.0", "--port", "8000"]
