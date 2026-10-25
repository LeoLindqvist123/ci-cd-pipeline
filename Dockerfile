FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    CHURN_MODEL_PATH=/app/outputs/modell.joblib

COPY pyproject.toml uv.lock ./
COPY src/ /app/src/
COPY outputs/ /app/outputs/

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "churn.api:app", "--host", "0.0.0.0", "--port", "8000"]
