# API Gateway --- Microservice Notification Distribution System

A production-ready **API Gateway** built with **Django REST Framework**,
designed to route requests to multiple backend microservices including
**User**, **Template**, and **Notification** services.

------------------------------------------------------------------------

## 🚀 Features

-   Reverse proxy routing for microservices
-   Redis-based caching & rate limiting
-   Circuit breaker for service resilience
-   JWT authentication middleware
-   Correlation ID & request logging
-   Observability with audit logs
-   Health check endpoint for service monitoring
-   Graceful handling of service downtime
-   Fully Dockerized

------------------------------------------------------------------------

## 🧱 Architecture Overview

Client → API Gateway → Microservices\
- User Service\
- Template Service\
- Notification Service

------------------------------------------------------------------------

## 📦 Tech Stack

-   Python 3.10
-   Django 5.x
-   Django REST Framework
-   Redis
-   PostgreSQL
-   Docker
-   Gunicorn

------------------------------------------------------------------------

## 🔧 Environment Variables

``` env
DEBUG=True
API_GATEWAY_SECRET_KEY=your-secret-key
API_GATEWAY_PORT=3000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

USER_SERVICE_URL=http://user-service:3001
TEMPLATE_SERVICE_URL=http://template-service:3002
NOTIFICATION_SERVICE_URL=http://notification-service:3005
```

------------------------------------------------------------------------

## 🛠 Local Setup

``` bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

------------------------------------------------------------------------

## 🐳 Docker Setup

### Build Image

``` bash
docker build -t api-gateway .
```

### Create Network

``` bash
docker network create micro-net
```

### Run Redis

``` bash
docker run -d --name redis --network micro-net -p 6379:6379 redis
```

### Run API Gateway

``` bash
docker run -d --name api-gateway --network micro-net --env-file .env -p 3000:3000 api-gateway
```

------------------------------------------------------------------------

## 🧪 Run Tests

``` bash
pytest
```

------------------------------------------------------------------------

## 🩺 Health Check

``` http
GET /api/v1/health/
```

------------------------------------------------------------------------

## 🔀 Gateway Routes

User Proxy:

``` http
/api/v1/users/*
/api/v1/auth/*
```

Template Proxy:

``` http
/api/v1/templates/*
```

Notification Gateway:

``` http
POST /api/v1/notifications/
```

Notification Service Proxy:

``` http
/api/v1/notifications/*
```

------------------------------------------------------------------------

## 🛡 Resilience

-   Returns graceful 503 when services fail
-   Circuit breaker prevents overload
-   Errors logged for observability

------------------------------------------------------------------------

## 👨🏽‍💻 Author

**Udeagha Mark Mang**\
Backend Engineer --- Python & Django

------------------------------------------------------------------------

## 📜 License

MIT License
