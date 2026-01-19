# Push Notification Service

A robust, scalable microservice for delivering push notifications to mobile devices (FCM) and web browsers (Web Push). Part of a distributed notification system architecture.

## Overview

The Push Service consumes notification requests from RabbitMQ, fetches user device tokens from the User Service, renders templates from the Template Service, and delivers push notifications through Firebase Cloud Messaging (FCM) or Web Push (VAPID).

### Key Features

- **Multi-Platform Support**: FCM (Android/iOS) and Web Push (PWA)
- **Asynchronous Processing**: RabbitMQ-based message queue consumer
- **Circuit Breaker Pattern**: Prevents cascading failures
- **Retry Mechanism**: Exponential backoff with configurable attempts
- **Rate Limiting**: Per-user notification throttling
- **Idempotency**: Prevents duplicate notifications
- **Rich Notifications**: Supports images, actions, and custom data
- **Dead Letter Queue**: Handles permanently failed messages
- **Health Monitoring**: Redis and RabbitMQ connectivity checks

## Architecture

```
API Gateway → RabbitMQ (push.queue)
                  ↓
            Push Service
                  ↓
         ┌────────┴────────┐
         ↓                 ↓
    User Service    Template Service
         ↓                 ↓
    (push_token)    (rendered content)
         ↓
    ┌────┴─────┐
    ↓          ↓
  FCM      Web Push
```

### Message Flow

1. API Gateway publishes `NotificationRequest` to RabbitMQ `push.queue`
2. Push Service consumes message from queue
3. Fetches user's push token from User Service (`GET /api/v1/users/{user_id}`)
4. Renders notification template from Template Service (`POST /api/v1/templates/render`)
5. Transforms to `PushNotificationRequest` with actual tokens and content
6. Sends to FCM or Web Push with circuit breaker protection
7. Reports delivery status via `/api/v1/push/status` endpoint

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker & Docker Compose
- Redis
- RabbitMQ
- Firebase project with FCM enabled

## Installation

### Install uv (Recommended)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Project

```bash
# Clone repository
cd push-service

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows

# Install dependencies from lock file (reproducible)
uv sync

# Or install directly from pyproject.toml
uv pip install -r pyproject.toml
```

### Managing Dependencies

```bash
# Add new dependency
# 1. Edit pyproject.toml, add to dependencies array
# 2. Update lock file
uv lock

# 3. Install
uv sync

# Development dependencies are in [tool.uv.dev-dependencies]
```

### Firebase Credentials Setup

**⚠️ Required for FCM notifications**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → **Project Settings** → **Service Accounts**
3. Click **Generate New Private Key**
4. Save as `credentials/firebase-adminsdk.json`

See [credentials/README.md](credentials/README.md) for detailed instructions.

**Note**: The credentials file is in `.gitignore` for security. Each team member must add their own credentials file.

```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME=Push Notification Service
ENVIRONMENT=development
DEBUG=true
PORT=8003

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=notifications.direct
RABBITMQ_PUSH_QUEUE=push.queue

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# User Service (manages push tokens)
USER_SERVICE_URL=http://user-service:8001
USE_DUMMY_DEVICE_TOKENS=true

# Template Service (renders notification content)
TEMPLATE_SERVICE_URL=http://template-service:8002
USE_DUMMY_TEMPLATES=true

# Firebase Cloud Messaging
FCM_ENABLED=true
FCM_CREDENTIALS_PATH=./credentials/firebase-adminsdk.json
FCM_PROJECT_ID=your-firebase-project-id

# Web Push (VAPID)
WEB_PUSH_ENABLED=true
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_SUBJECT=mailto:admin@example.com

# Circuit Breaker & Retry
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
MAX_RETRY_ATTEMPTS=3
RETRY_INITIAL_DELAY=1.0

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### Firebase Setup

1. Create Firebase project at https://console.firebase.google.com
2. Generate service account key: Project Settings → Service Accounts → Generate new private key
3. Save as `credentials/firebase-adminsdk.json`
4. Add FCM credentials to `.env`

### Web Push (VAPID) Setup

```bash
# Generate VAPID keys
npx web-push generate-vapid-keys

# Add keys to .env
VAPID_PRIVATE_KEY=<your-private-key>
VAPID_PUBLIC_KEY=<your-public-key>
```

## Running the Service

### Local Development

```bash
# Start dependencies (Redis & RabbitMQ)
# Use the root-level docker-compose.yml or run these individually

# Run the service
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### With Docker

```bash
# Build the image
docker build -t push-service:latest .

# Run container (mount credentials)
docker run -d \
  -p 8003:8003 \
  -v $(pwd)/credentials/firebase-adminsdk.json:/app/credentials/firebase-adminsdk.json:ro \
  --env-file .env \
  --name push-service \
  push-service:latest
```

### With Docker Compose

**Note**: The docker-compose.yml is at the root level for all microservices. See [docker-compose.yml.example](docker-compose.yml.example) for reference configuration.

From the root directory:
```bash
# Start all services
docker-compose up --build

# Start only push-service and its dependencies
docker-compose up push-service

# Stop services
docker-compose down
```

## API Endpoints

### Health Check
```
GET /api/v1/health
```
Returns service health status including Redis and RabbitMQ connectivity.

### Status Reporting
```
POST /api/v1/push/status
```
Report push notification delivery status.

**Request Body:**
```json
{
  "notification_id": "req-123",
  "status": "delivered",
  "timestamp": "2026-01-15T10:30:00Z",
  "error": null
}
```

**Status Values:**
- `delivered`: Successfully delivered
- `pending`: In progress
- `failed`: Delivery failed

### API Documentation (Development)

When `DEBUG=true`:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## Message Format

### Input (from API Gateway via RabbitMQ)

```json
{
  "notification_type": "push",
  "user_id": "user-123",
  "template_code": "welcome",
  "variables": {
    "name": "John Doe",
    "link": "https://example.com/welcome",
    "meta": {"campaign": "onboarding"}
  },
  "request_id": "req-456",
  "priority": 1,
  "metadata": {"language": "en"}
}
```

### Transformed Message (internal)

```json
{
  "notification_id": "req-456",
  "user_id": "user-123",
  "device_tokens": ["fcm-token-abc123"],
  "platform": "fcm",
  "notification": {
    "title": "Welcome John Doe!",
    "body": "Thanks for joining us, John Doe. Get started now!",
    "click_action": "https://example.com/welcome",
    "image_url": null,
    "custom_data": {"campaign": "onboarding"}
  },
  "priority": "normal",
  "ttl": 86400
}
```

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_push_service.py -v

# Run tests matching pattern
pytest tests/ -k "fcm" -v
```

### Test Coverage

The test suite includes:
- **Unit Tests**: Individual service components (FCM, Web Push, Redis, Circuit Breaker)
- **Integration Tests**: End-to-end notification flow
- **Client Tests**: User Service and Template Service integrations
- **Consumer Tests**: RabbitMQ message processing

Test files:
- `tests/test_fcm_service.py` - Firebase Cloud Messaging
- `tests/test_web_push_service.py` - Web Push notifications
- `tests/test_push_service.py` - Main push service logic
- `tests/test_redis_client.py` - Redis operations and idempotency
- `tests/test_circuit_breaker.py` - Circuit breaker pattern
- `tests/test_consumer.py` - RabbitMQ consumer
- `tests/test_device_token_client.py` - User Service integration
- `tests/test_template_client.py` - Template Service integration
- `tests/test_integration.py` - End-to-end scenarios
- `tests/test_health.py` - Health check endpoint

### Code Quality

```bash
# Run linter and formatter
uv run ruff check --fix .
uv run ruff format .

# Check without fixing
uv run ruff check .

# Type checking (if mypy configured)
mypy app/
```

### Get FCM Device Token

1. Copy `get-fcm-token.html.example` to `get-fcm-token.html`
2. Add your Firebase config
3. Open in browser and click "Get Device Token"
4. Use token for testing

### Test Push Notification

```bash
# Publish test message to RabbitMQ
curl -u guest:guest -X POST http://localhost:15672/api/exchanges/%2F/notifications.direct/publish \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {},
    "routing_key": "push",
    "payload": "{\"notification_type\":\"push\",\"user_id\":\"test-user\",\"template_code\":\"welcome\",\"variables\":{\"name\":\"Test User\",\"link\":\"https://example.com\"},\"request_id\":\"test-123\",\"priority\":1}",
    "payload_encoding": "string"
  }'
```

## Monitoring

### Logs

```bash
# View logs
docker-compose logs -f push-service

# Filter by level
docker-compose logs -f push-service | grep ERROR
```

### Metrics

The service tracks:
- Total notifications processed
- Success/failure counts
- Circuit breaker status
- Queue processing time

### Health Check

```bash
curl http://localhost:8003/api/v1/health
```

## Troubleshooting

### Service Won't Start

- Check Redis connection: `redis-cli ping`
- Check RabbitMQ: http://localhost:15672 (guest/guest)
- Verify `.env` file exists and has correct values
- Check Firebase credentials path

### Notifications Not Sending

- Verify User Service is running and has user's push token
- Check Template Service is running
- Verify FCM credentials are valid
- Check device token is active
- Review logs for circuit breaker status

### Performance Issues

- Increase `RABBITMQ_PREFETCH_COUNT` for parallel processing
- Adjust `MAX_RETRY_ATTEMPTS` and retry delays
- Scale horizontally by running multiple instances
- Check Redis and RabbitMQ performance

## Integration with Other Services

### User Service
- **Purpose**: Provides user's push token
- **Endpoint**: `GET /api/v1/users/{user_id}`
- **Config**: `USER_SERVICE_URL`

### Template Service
- **Purpose**: Renders notification content
- **Endpoint**: `POST /api/v1/templates/render`
- **Config**: `TEMPLATE_SERVICE_URL`

### API Gateway
- **Purpose**: Publishes notification requests
- **Queue**: `notifications.direct` → `push.queue`

## Deployment

### Docker Build

```bash
docker build -t push-service:1.0.0 .
```

### Scale Horizontally

```bash
# Run multiple instances
docker-compose up --scale push-service=3
```
