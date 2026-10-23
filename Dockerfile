FROM python:3.11-slim

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHURN_MODEL_PATH=/app/outputs/modell.joblib

# Copy project metadata and source code needed for editable package installation
COPY pyproject.toml uv.lock ./
COPY src/ /app/src/
COPY outputs/ /app/outputs/

# Install dependencies including the churn package
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Start FastAPI service
CMD ["uv", "run", "uvicorn", "churn.api:app", "--host", "0.0.0.0", "--port", "8000"]