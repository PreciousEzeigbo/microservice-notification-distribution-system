FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

ENV UV_SYSTEM_PYTHON=1

RUN groupadd -r appuser && useradd -r -g appuser appuser && chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser pyproject.toml README.md ./
RUN uv sync --no-cache

COPY --chown=appuser:appuser ./app ./app
RUN mkdir -p ./credentials

EXPOSE 8003

ENV PYTHONUNBUFFERED=1

USER appuser

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
