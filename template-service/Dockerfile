FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser


ENV PORT=3002
EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
        CMD python -c "import os, urllib.request; port = os.getenv('PORT', '3002'); urllib.request.urlopen(f'http://localhost:{port}/api/v1/templates/health/', timeout=5).read()"


CMD ["/bin/sh", "-c", "gunicorn template_service.wsgi:application --bind 0.0.0.0:$PORT --workers ${GUNICORN_WORKERS:-4}"]
# ---

