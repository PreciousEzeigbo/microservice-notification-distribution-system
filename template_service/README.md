# Template Service - Django/Python

A production-ready email template microservice built with Django REST Framework, designed to integrate seamlessly with the NestJS Email Service in the Notification Distribution System.

## Overview

The Template Service manages email templates with Handlebars placeholder support. It provides a REST API for creating, retrieving, updating, and validating email templates used by the Email Service.

## Features

✨ **Template Management**
- Full CRUD operations for email templates
- Handlebars placeholder support (`{{variable}}`)
- Automatic placeholder extraction
- Template versioning and history tracking
- Active/inactive status management

🔍 **Validation**
- Template variable validation
- Required vs optional variables
- Placeholder extraction and validation
- Name format validation (snake_case)

📊 **Template Types**
- Welcome emails
- Password reset
- Transactional emails
- Promotional emails
- General notifications

🏥 **Production‑Ready**
- Health check endpoints
- Snake_case API responses (matches NestJS service)
- PostgreSQL database
- Docker support
- Comprehensive error handling

## Tech Stack

- **Framework**: Django 5.0, Django REST Framework 3.14
- **Database**: PostgreSQL 15
- **Template Engine**: Pybars3 (Handlebars for Python)
- **Web Server**: Gunicorn
- **Testing**: pytest, pytest-django
- **Code Quality**: Black, Flake8, isort

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- pip/virtualenv

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Seed sample templates
python manage.py seed_templates

# Run development server
python manage.py runserver 3002
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run migrations in container
docker-compose exec template-service python manage.py migrate

# Seed templates
docker-compose exec template-service python manage.py seed_templates
```

## API Endpoints

Base URL: `http://localhost:3002/api/v1`

### Template Management

#### List Templates
```http
GET /api/v1/templates/
Query params: ?is_active=true&template_type=welcome
```

#### Get Template
```http
GET /api/v1/templates/{name}/
```

#### Create Template
```http
POST /api/v1/templates/
Content-Type: application/json

{
  "name": "welcome_email",
  "template_type": "welcome",
  "subject": "Welcome {{user.name}}!",
  "html_content": "<h1>Hello {{user.name}}</h1>",
  "text_content": "Hello {{user.name}}",
  "description": "Welcome email template",
  "required_variables": ["user.name", "user.email"],
  "is_active": true
}
```

#### Update Template
```http
PUT /api/v1/templates/{name}/
PATCH /api/v1/templates/{name}/
```

#### Delete Template
```http
DELETE /api/v1/templates/{name}/
```

### Template Actions

#### Validate Template Variables
```http
POST /api/v1/templates/{name}/validate/

{
  "variables": {
    "user": {"name": "John", "email": "john@example.com"}
  }
}

Response:
{
  "valid": true,
  "template_name": "welcome_email",
  "message": "All required variables provided"
}
```

#### Get Placeholders
```http
GET /api/v1/templates/{name}/placeholders/

Response:
{
  "template_name": "welcome_email",
  "placeholders": ["user.name", "user.email"],
  "required_variables": ["user.name", "user.email"],
  "optional_variables": []
}
```

#### Get Version History
```http
GET /api/v1/templates/{name}/versions/

Response:
{
  "template_name": "welcome_email",
  "current_version": 3,
  "versions": [...]
}
```

#### Activate/Deactivate Template
```http
POST /api/v1/templates/{name}/activate/
POST /api/v1/templates/{name}/deactivate/
```

### Health Check
```http
GET /api/v1/templates/health/

Response:
{
  "status": "healthy",
  "timestamp": "2026-01-14T10:30:00Z",
  "database": {
    "status": "connected",
    "templates_count": 15
  }
}
```

## Integration with Email Service

The Email Service (NestJS) fetches templates from this service:

```typescript
// Email Service calls this endpoint
GET http://localhost:3002/api/v1/templates/welcome_email/

// Response matches snake_case convention
{
  "id": 1,
  "name": "welcome_email",
  "template_type": "welcome",
  "subject": "Welcome {{user.name}}!",
  "html_content": "<h1>Hello {{user.name}}</h1>",
  "required_variables": ["user.name"],
  "is_active": true,
  "version": 2
}
```

### Circuit Breaker Integration

The Email Service uses circuit breakers when calling this Template Service. Ensure:
- Health endpoint responds within 5 seconds
- Service returns proper HTTP status codes
- Database is properly configured and connected

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=templates --cov-report=html

# Run specific test file
pytest tests.py

# Run with verbose output
pytest -v
```

## Code Quality

```bash
# Format code with Black
black .

# Check code style with Flake8
flake8 .

# Sort imports with isort
isort .

# Run all quality checks
black . && isort . && flake8 .
```


## Environment Variables
```bash
# Django settings
DJANGO_SECRET_KEY=<generate-a-secure-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
# Database
DB_NAME=template_service
DB_USER=postgres
DB_PASSWORD=<your-password>
DB_HOST=localhost
DB_PORT=5432
# Application
PORT=3002

## Monitoring

### Health Checks

The service provides a health endpoint that checks:
- Database connectivity
- Template count
- Service status

### Logging

Structured logging is configured for:
- Template operations (create, update, delete)
- Validation errors
- Health check failures

## Snake_case Convention

All API responses use snake_case to match the NestJS Email Service:

```json
{
  "template_name": "welcome_email",
  "is_active": true,
  "created_at": "2026-01-14T10:30:00Z",
  "required_variables": ["user.name"]
}
```

## Contributing

1. Follow Django and PEP 8 conventions
2. Use snake_case for all API responses
3. Write tests for new features
4. Run code quality checks before committing
5. Update documentation for API changes

## License

Part of the Notification Distribution System
 