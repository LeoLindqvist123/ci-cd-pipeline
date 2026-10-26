FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
COPY src/ /app/src/
COPY outputs/ /app/outputs/

RUN uv sync --frozen --no-dev \
    && if [ -f /app/outputs/modell.joblib ] && [ ! -f /app/outputs/model.joblib ]; then cp /app/outputs/modell.joblib /app/outputs/model.joblib; fi \
    && if [ -f /app/outputs/model.joblib ] && [ ! -f /app/outputs/modell.joblib ]; then cp /app/outputs/model.joblib /app/outputs/modell.joblib; fi \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "churn.api:app", "--host", "0.0.0.0", "--port", "8000"]
