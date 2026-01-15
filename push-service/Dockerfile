FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_SYSTEM_PYTHON=1

# Install dependencies
COPY pyproject.toml ./
RUN uv pip install --no-cache -r pyproject.toml

# Copy application code
COPY ./app ./app

# Create credentials directory
# Firebase credentials should be mounted at runtime via volume:
# -v /path/to/firebase-adminsdk.json:/app/credentials/firebase-adminsdk.json:ro
# See credentials/README.md for setup instructions
RUN mkdir -p ./credentials

EXPOSE 8003

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]
