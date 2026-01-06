# Email Service API Contract

**Version:** 1.0  
**Service:** email-service  
**Owner:** [Your Name/Team]  
**Last Updated:** January 6, 2026

## Overview
The Email Service consumes messages from RabbitMQ, processes email notifications, and communicates with other services via HTTP.

---

## 1. RabbitMQ Message Contract

### Queue Information
- **Exchange:** `notifications.direct`
- **Queue Name:** `email.queue`
- **Routing Key:** `notification.email`
- **DLX Exchange:** `notifications.dlx`
- **DLX Routing Key:** `failed.email`

### Message Format
```json
{
  "message_id": "string (UUID)",
  "request_id": "string (UUID)",
  "notification_type": "email",
  "user_id": "string (UUID)",
  "template_code": "string",
  "variables": {
    "name": "string",
    "link": "string (URL)",
    // ... other variables as needed
  },
  "priority": "number (optional, 1-3)",
  "metadata": {
    "source": "string (optional)",
    "campaign_id": "string (optional)"
  },
  "correlation_id": "string (UUID, optional)",
  "created_at": "string (ISO 8601, optional)"
}
```

### Example Message
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "client-req-123",
  "notification_type": "email",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "template_code": "welcome_email",
  "variables": {
    "name": "John Doe",
    "link": "https://app.example.com/verify"
  },
  "priority": 1,
  "metadata": {
    "source": "user_signup"
  },
  "correlation_id": "abc-123-xyz",
  "created_at": "2026-01-06T10:00:00Z"
}
```

---

## 2. HTTP APIs We Call

### A. User Service

**Endpoint:** `GET /api/v1/users/{userId}`

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "name": "string",
    "email": "string (email)",
    "push_token": "string (optional)",
    "preferences": {
      "email": boolean,
      "push": boolean
    }
  },
  "message": "string"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "string",
  "message": "string"
}
```

### B. Template Service

**Endpoint:** `GET /api/v1/templates/{templateCode}`

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "code": "string",
    "subject": "string (with {{handlebars}} placeholders)",
    "body": "string (HTML with {{handlebars}} placeholders)",
    "text_version": "string (optional, plain text)",
    "language": "string",
    "version": number
  },
  "message": "string"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "string",
  "message": "string"
}
```

### C. API Gateway

**Endpoint:** `POST /api/v1/notifications/{messageId}/status`

**Request Body:**
```json
{
  "notification_id": "string (UUID)",
  "status": "delivered | failed | pending",
  "timestamp": "string (ISO 8601)",
  "error": "string (optional)",
  "provider_response": {
    "success": boolean,
    "messageId": "string (optional)",
    "provider": "string"
  }
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "string"
}
```

---

## 3. Health Check Endpoint

**Endpoint:** `GET /api/v1/email/health`

**Response:**
```json
{
  "service": "email-service",
  "rabbitmq": boolean,
  "smtp": boolean,
  "externalServices": {
    "userService": boolean,
    "templateService": boolean,
    "apiGateway": boolean
  },
  "timestamp": "string (ISO 8601)"
}
```

---

## 4. Error Handling

### Retry Logic
- Messages that fail processing are **nack'd** and go to the Dead Letter Queue (DLQ)
- No automatic retries within the service (implement via RabbitMQ TTL if needed)

### Status Updates
- All notification status updates are sent to API Gateway
- Even on failure, we attempt to update status (non-blocking)

---

## 5. Required Environment Variables

These values must be provided by other teams:

| Variable | Description | Example |
|----------|-------------|---------|
| `USER_SERVICE_URL` | User Service base URL | `http://user-service:3001` |
| `TEMPLATE_SERVICE_URL` | Template Service base URL | `http://template-service:3002` |
| `API_GATEWAY_URL` | API Gateway base URL | `http://api-gateway:3000` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@rabbitmq:5672` |

---

## 6. Questions for Other Teams

Please help us fill in these details:

1. **Authentication:** How do services authenticate with each other? API keys? JWT? Mutual TLS?
2. **Rate Limits:** Are there any rate limits on the User/Template/Gateway APIs?
3. **Timeouts:** What's the expected response time for each service?
4. **Service Discovery:** Are we using DNS, Consul, or hardcoded URLs?
5. **Error Codes:** What HTTP status codes should we expect and handle?
6. **Deployment Order:** Which services need to start first?
7. **Testing Environment:** Where can we test integration with other services?

---

## 7. Contact

**Service Owner:** [Your Name]  
**Email:** [your-email@example.com]  
**Slack/Discord:** [@yourhandle]  
**Repository:** [link to repo]

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial contract |

