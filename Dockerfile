FROM python:3.11-slim

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHURN_MODEL_PATH=/app/outputs/modell.joblib

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-dev

# Copy application source and project structure
COPY src/ /app/src/
COPY outputs/ /app/outputs/

# Expose API port
EXPOSE 8000

# Start FastAPI application
CMD ["uv", "run", "uvicorn", "churn.api:app", "--host", "0.0.0.0", "--port", "8000"]