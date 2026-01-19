# User Service

The **User Service** is a core microservice responsible for managing users, authentication, and notification preferences in the Notification Distribution System.

It provides APIs for:
- User registration
- User authentication (JWT)
- Retrieving user details
- Managing notification preferences

---

## 🚀 Features

- Custom user model with **UUID primary key**
- Email-based authentication (no username)
- JWT authentication (access & refresh tokens)
- User notification preferences (email & push)
- Health check endpoint for monitoring
- Fully tested with Django REST Framework
- Dockerised for deployment
- Environment-based configuration

---

## 🛠 Tech Stack

- **Python** 3.10+
- **Django** 4.2
- **Django REST Framework**
- **Simple JWT**
- **PostgreSQL** (Supabase)
- **Docker**

---

## 📁 Project Structure

```text
user-service/
├── accounts/
├── user_service/
├── manage.py
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Environment Variables

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@host:5432/dbname
DEBUG=True
PORT=3001
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

---

## ▶️ Running the Service Locally

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:3001
```

---

## 🐳 Running with Docker

```bash
docker build -t user-service .
docker run --env-file .env -p 3001:3001 user-service
```

---

## 🧪 Running Tests

```bash
python manage.py test
```

---

## 🔑 API Endpoints

GET  /api/v1/health/
POST /api/v1/users/
POST /api/v1/auth/login/
GET  /api/v1/users/{user_id}/

---

## 👤 Author

Udeagha Mark Mang
