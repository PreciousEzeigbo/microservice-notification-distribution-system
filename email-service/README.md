# Email Service

A production-ready email notification microservice built with NestJS, featuring advanced reliability patterns including circuit breakers, retry logic, dead-letter queues, and health-aware message reprocessing.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [Error Handling](#error-handling)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Testing](#testing)
- [Code Quality](#code-quality)

## Overview

The Email Service is a robust microservice responsible for processing and sending email notifications within the Notification Distribution System. It consumes messages from RabbitMQ, validates templates, compiles dynamic content using Handlebars, and sends emails via SMTP with comprehensive error handling and retry mechanisms.

## Features

### 🛡️ Production-Grade Reliability

- **Circuit Breaker Pattern**: Protects against cascading failures when external services (User Service, Template Service, API Gateway) are unavailable
  - Configurable thresholds and timeouts
  - Automatic state transitions (CLOSED → OPEN → HALF_OPEN)
  - Per-service circuit breaker instances

- **Advanced Retry Logic**: RabbitMQ-based retry mechanism using TTL and dead-letter exchanges
  - Exponential backoff with configurable delays (default: 5000ms)
  - Maximum retry attempts (default: 3)
  - Automatic message requeuing with retry count tracking

- **Dead Letter Queue (DLQ)**: Failed messages are moved to DLQ after max retries
  - Health-aware automatic reprocessing
  - Checks dependent services every 5 minutes
  - Only logs when health status changes to reduce noise

### 📧 Email Processing

- **Template Management**: Fetches dynamic templates from Template Service
  - Handlebars compilation and variable substitution
  - Automatic placeholder extraction and validation
  - Throws errors for missing required variables

- **SMTP Provider**: Reliable email delivery using Nodemailer
  - Connection verification on startup
  - Configurable SMTP settings via environment variables
  - Production-ready error handling

### 🔍 Observability

- **Health Checks**: 
  - SMTP connection verification
  - External service health monitoring (User Service, Template Service, API Gateway)
  - Detailed health status reporting

- **Structured Logging**: Production-grade logging with context
  - Request/message tracking with unique IDs
  - Error stack traces with correlation
  - Log-level filtering based on events

### ✅ Code Quality

- **Snake_case Convention**: All API responses, error messages, and internal properties use snake_case
- **Global Exception Filters**: Centralized error handling with standardized response formats
- **Type Safety**: Full TypeScript implementation with strict typing
- **Prettier Formatting**: Consistent code style across the codebase

## Architecture

```
┌─────────────────┐
│   RabbitMQ      │
│  (Main Queue)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Email Consumer                │
│  - Message validation           │
│  - Retry tracking               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Email Processor               │
│  - Circuit breaker protection   │
│  - Template validation          │
│  - User data fetching           │
│  - Email compilation            │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   SMTP Email Provider           │
│  - Nodemailer integration       │
│  - Connection management        │
└─────────────────────────────────┘

External Dependencies (Circuit Breaker Protected):
- User Service (http://localhost:3001)
- Template Service (http://localhost:3002)
- API Gateway (http://localhost:3000)
```

### Message Flow

1. **Message Reception**: Consumer receives notification message from RabbitMQ main queue
2. **Validation**: Message structure and required fields are validated
3. **Template Fetching**: Retrieves template from Template Service (circuit breaker protected)
4. **Placeholder Validation**: Extracts template variables and validates against message data
5. **User Data**: Fetches user details from User Service (circuit breaker protected)
6. **Email Compilation**: Compiles template with Handlebars using user data and message variables
7. **Email Sending**: Sends email via SMTP provider
8. **Status Update**: Updates notification status in API Gateway (circuit breaker protected)
9. **Retry/DLQ**: On failure, message is retried up to 3 times with 5-second delays, then moved to DLQ

### DLQ Reprocessing

- **Health Monitoring**: Checks dependent services every 5 minutes
- **Automatic Recovery**: When all services are healthy, messages are reprocessed from DLQ
- **Smart Logging**: Only logs when health status changes (healthy ↔ unhealthy)

## Tech Stack

- **Framework**: NestJS 11.x
- **Language**: TypeScript 5.7.x
- **Message Queue**: RabbitMQ (amqplib)
- **Email Provider**: Nodemailer
- **Template Engine**: Handlebars
- **HTTP Client**: Axios (@nestjs/axios)
- **Validation**: class-validator, class-transformer
- **Documentation**: Swagger/OpenAPI
- **Testing**: Jest
- **Code Quality**: ESLint, Prettier

## Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm or yarn
- RabbitMQ server
- SMTP server (Gmail, SendGrid, or local SMTP for development)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd email-service

# Install dependencies
npm install
```

## Configuration

Create a `.env` file in the root directory:

```env
# Application
NODE_ENV=development
PORT=3003

# RabbitMQ
RABBITMQ_URL=amqp://localhost:5672
RABBITMQ_QUEUE=email-notifications
RABBITMQ_DLQ=email-notifications-dlq
RABBITMQ_RETRY_QUEUE=email-notifications-retry

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=noreply@yourapp.com

# External Services
USER_SERVICE_URL=http://localhost:3001
TEMPLATE_SERVICE_URL=http://localhost:3002
API_GATEWAY_URL=http://localhost:3000

# Circuit Breaker Configuration (Optional)
CIRCUIT_BREAKER_TIMEOUT=5000
CIRCUIT_BREAKER_ERROR_THRESHOLD=5
CIRCUIT_BREAKER_RESET_TIMEOUT=30000

# Retry Configuration (Optional)
MAX_RETRY_ATTEMPTS=3
INITIAL_RETRY_DELAY=5000
```

### Configuration Constants

The service uses centralized configuration in `src/shared/constants/queue.constants.ts`:

```typescript
RETRY_CONFIG = {
  MAX_RETRIES: 3,
  INITIAL_DELAY: 5000, // Must match RabbitMQ queue TTL
}

CIRCUIT_BREAKER_CONFIG = {
  TIMEOUT: 5000,
  ERROR_THRESHOLD: 5,
  RESET_TIMEOUT: 30000,
}
```

## Running the Application

### Development Mode

```bash
# Watch mode with auto-reload
npm run start:dev
```

### Debug Mode

```bash
# Debug mode with auto-reload
npm run start:debug
```

### Production Mode

```bash
# Build the application
npm run build

# Run in production mode
npm run start:prod
```

The service will be available at:
- **API**: http://localhost:3003
- **Swagger Docs**: http://localhost:3003/api/docs

## Docker Deployment

### Building the Docker Image

```bash
# Build the image
docker build -t email-service:latest .

# Run the container
docker run -p 3003:3003 --env-file .env email-service:latest
```

### Using Docker Compose

The service is designed to work with the main `docker-compose.yml` at the repository root:

```bash
# From the repository root
docker-compose up email-service
```

The Dockerfile includes:
- Multi-stage build for optimized image size
- Production dependencies only
- Health check endpoint
- Non-root user for security

## API Documentation

### Swagger UI

Interactive API documentation is available at: http://localhost:3003/api/docs

### Key Endpoints

#### Health Check
```http
GET /health
```

Response (snake_case):
```json
{
  "status": "ok",
  "timestamp": "2026-01-08T02:00:00.000Z",
  "uptime": 12345,
  "services": {
    "smtp": {
      "status": "healthy",
      "message": "SMTP connection verified"
    },
    "user_service": {
      "status": "healthy"
    },
    "template_service": {
      "status": "unhealthy",
      "error": "Connection refused"
    },
    "api_gateway": {
      "status": "healthy"
    }
  }
}
```

#### Send Email (Direct)
```http
POST /email/send
Content-Type: application/json

{
  "message_id": "msg_123",
  "request_id": "req_123",
  "user_id": "user_123",
  "to": "user@example.com",
  "template_id": "welcome",
  "variables": {
    "name": "John Doe",
    "activation_link": "https://app.com/activate/token"
  }
}
```

## Error Handling

### Standardized Error Responses

All errors follow a consistent snake_case format:

```json
{
  "status_code": 503,
  "message": "User Service is currently unavailable",
  "error": "Service Unavailable",
  "details": "ECONNREFUSED",
  "timestamp": "2026-01-08T02:00:00.000Z",
  "path": "/email/send"
}
```

### Exception Types

- **MessageValidationException**: Invalid message format or missing required fields
- **ServiceUnavailableException**: External service unavailable (triggers circuit breaker)
- **HttpException**: Generic HTTP errors with proper status codes

### Circuit Breaker States

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service failed threshold reached, requests fail immediately
- **HALF_OPEN**: Testing if service recovered, limited requests allowed

## Monitoring & Health Checks

### Service Health

Monitor the health of the email service and its dependencies:

```bash
curl http://localhost:3003/api/v1/email/health
```

### RabbitMQ Monitoring

Access RabbitMQ Management UI:
- URL: http://localhost:15672
- Default credentials: guest/guest

Monitor queues:
- `email-notifications` - Main queue
- `email-notifications-retry` - Retry queue with TTL
- `email-notifications-dlq` - Dead letter queue

### Logs

The service provides structured logging with different levels:

- **LOG**: Normal operations (message received, processed, sent)
- **WARN**: Recoverable issues (retry attempts, circuit breaker open)
- **ERROR**: Failures (processing errors, SMTP errors, service unavailable)

## Testing

### Unit Tests

```bash
npm run test
```

### Test Coverage

```bash
npm run test:cov
```

Coverage reports are generated in the `coverage/` directory.

### End-to-End Tests

```bash
npm run test:e2e
```

### Watch Mode

```bash
npm run test:watch
```

## Code Quality

### Linting

```bash
# Run ESLint
npm run lint
```

### Formatting

```bash
# Format code with Prettier
npm run format

# Check formatting without changes
npm run format:check
```

### Type Checking

```bash
# Run TypeScript compiler check
npm run type-check
```

### Pre-commit Hooks

The project uses Prettier to maintain consistent code style. Run `npm run format` before committing changes.

## Project Structure

```
email-service/
├── src/
│   ├── common/
│   │   ├── exceptions/          # Custom exception classes
│   │   ├── filters/             # Global exception filters
│   │   └── utils/               # Utilities (circuit breaker)
│   ├── config/                  # Configuration files
│   ├── constants/               # System constants and messages
│   ├── email/
│   │   ├── consumers/           # RabbitMQ consumers and DLQ reprocessor
│   │   ├── http/                # External service clients
│   │   ├── processors/          # Email processing logic
│   │   ├── providers/           # SMTP provider implementation
│   │   ├── email.controller.ts  # REST API controller
│   │   ├── email.service.ts     # Business logic
│   │   └── email.module.ts      # Module definition
│   ├── shared/
│   │   ├── constants/           # Queue and retry configuration
│   │   └── interfaces/          # TypeScript interfaces
│   ├── app.module.ts            # Root module
│   └── main.ts                  # Application entry point
├── test/                        # Test files
├── Dockerfile                   # Docker configuration
├── .env                         # Environment variables
├── package.json                 # Dependencies and scripts
└── README.md                    # This file
```

## Contributing

1. Follow the existing code style (snake_case for API responses, camelCase for internal TypeScript.)
2. Run `npm run format` before committing
3. Ensure all tests pass with `npm run test`
4. Update documentation for new features

## License

This project is part of the Notification Distribution System.
