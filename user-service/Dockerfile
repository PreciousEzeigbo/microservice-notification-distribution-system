# -----------------------------
# Base image
# -----------------------------
FROM python:3.10-slim

# -----------------------------
# Environment variables
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Set work directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# -----------------------------
# Copy project files
# -----------------------------
COPY . .

# -----------------------------
# Expose service port
# -----------------------------
EXPOSE 3001

# -----------------------------
# Run Django development server
# (PORT is read from .env / environment)
# -----------------------------
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-3001} user_service.wsgi:application"]
