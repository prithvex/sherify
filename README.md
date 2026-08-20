# Automated Mass Campaign Manager (Sherify)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org)
[![Alembic](https://img.shields.io/badge/Alembic-1.13+-orange.svg)](https://alembic.sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com)

> **Current Implementation Status**: **V1 — Audience Management Completed.**

---

## 📖 Project Purpose

The **Automated Mass Campaign Manager** is a high-scale, production-oriented email campaign system engineered to manage audiences, execute high-volume campaigns, track engagement, and ensure email compliance.

---

## 🏛️ Architecture & Design Pattern

The system strictly enforces a 4-tier layered architecture to maintain thin routes, strict separation of concerns, and robust business logic encapsulation:

```
┌────────────────────────────────────────────────────────┐
│                   Router Layer                         │
│   (HTTP parsing, Pydantic DTOs, dependency injection)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Service Layer                        │
│ (Business logic, ownership validation, JWT & hashing)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Repository Layer                      │
│     (Async queries, pagination, DB filter logic)       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Database Layer                        │
│    (PostgreSQL 16, UUIDs, Foreign Keys, Constraints)   │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
sherify/
├── alembic/                    # Async database migration scripts
│   ├── versions/               # Migration version files (001_initial_v1, etc.)
│   ├── env.py                  # Alembic environment runner
│   └── script.py.mako          # Migration template
├── app/                        # Application core package
│   ├── api/                    # API router layer
│   │   ├── v1/                 # API Version 1
│   │   │   ├── endpoints/      # Specific endpoints (auth, users, contact_lists, health)
│   │   │   └── api.py          # V1 router aggregation
│   │   └── deps.py             # FastAPI dependencies (get_db, get_current_user, get_current_active_user)
│   ├── core/                   # Core application configuration & security
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # Async SQLAlchemy engine & sessionmaker
│   │   └── security.py         # Password hashing (bcrypt) & JWT helpers
│   ├── models/                 # SQLAlchemy 2.x declarative models
│   │   ├── base.py             # Base model, UUIDMixin, TimestampMixin
│   │   ├── user.py             # User entity
│   │   ├── contact_list.py     # ContactList entity
│   │   └── subscriber.py       # Subscriber entity with per-list uniqueness
│   ├── repositories/           # Data access repository layer
│   │   ├── user_repo.py        # User queries
│   │   ├── contact_list_repo.py# ContactList queries & pagination
│   │   └── subscriber_repo.py  # Subscriber queries & pagination
│   ├── schemas/                # Pydantic validation models & DTOs
│   │   ├── common.py           # Pagination schemas (PaginatedResponse, PaginationParams)
│   │   ├── user.py             # User DTOs (Register, Login, Token, Response)
│   │   ├── contact_list.py     # ContactList DTOs (Create, Update, Response)
│   │   ├── subscriber.py       # Subscriber DTOs (Create, Update, Response, Status Enum)
│   │   └── health.py           # Health check response schemas
│   └── main.py                 # FastAPI application, lifespan, CORS, and root health check
├── tests/                      # Pytest async test suite
│   ├── conftest.py             # Fixtures, test database lifecycle, test client
│   ├── test_auth.py            # Registration, login, password security tests
│   ├── test_users.py           # Profile & token authorization tests
│   ├── test_contact_lists.py   # Contact list CRUD & cross-user isolation tests
│   ├── test_subscribers.py     # Subscriber CRUD, per-list uniqueness & filter tests
│   ├── test_database_constraints.py # Cascade deletion & FK integrity tests
│   └── test_health.py          # System health check tests
├── .env.example                # Example environment variables
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Multi-container orchestration (API, PostgreSQL, Redis)
├── Dockerfile                  # Production container definition
├── memory.md                   # Engineering memory & version status tracker
├── pyproject.toml              # Build & test configuration
├── README.md                   # Developer guide & API reference
└── requirements.txt            # Minimal async application dependencies
```

---

## 🚀 Environment Setup & Installation

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 16 (or Docker)
- Redis 7 (or Docker)

### 2. Environment Configuration
Copy the example environment configuration:
```bash
cp .env.example .env
```

### 3. Local Virtual Environment Setup
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

### 4. Database Migrations
Apply database migrations using Alembic:
```bash
# Apply all migrations
alembic upgrade head

# Rollback migration (if needed)
alembic downgrade base
```

### 5. Running the Application Locally
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🐳 Docker Setup

To run the complete production-like stack using Docker Compose:

```bash
# Start all containers in background
docker compose up --build -d

# View container status
docker compose ps

# View real-time logs
docker compose logs -f api
```

The stack includes:
- `api` — FastAPI application on port `8000`
- `postgres` — PostgreSQL 16 database with health check
- `redis` — Redis 7 cache & broker with health check

---

## 🧪 Testing

The repository features comprehensive integration and unit tests covering authentication, authorization, ownership isolation, pagination, filters, and database constraints.

Run the complete test suite:
```bash
pytest -v
```

---

## 📡 API Reference (V1 Endpoints)

### 1. Authentication & Users
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register a new user account | No |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token | No |
| `GET` | `/api/v1/users/me` | Retrieve authenticated user profile | Bearer Token |

### 2. Contact Lists
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contact-lists` | Create a new contact list | Bearer Token |
| `GET` | `/api/v1/contact-lists` | List user's contact lists (paginated) | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}` | Get single contact list by ID | Bearer Token |
| `PATCH` | `/api/v1/contact-lists/{list_id}` | Update contact list details | Bearer Token |
| `DELETE` | `/api/v1/contact-lists/{list_id}` | Delete contact list & cascade delete subscribers | Bearer Token |

### 3. Subscribers (Nested under Contact Lists)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contact-lists/{list_id}/subscribers` | Add subscriber to contact list | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers` | List subscribers (paginated, filtered) | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Get subscriber by ID | Bearer Token |
| `PATCH` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Update subscriber details | Bearer Token |
| `DELETE` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Remove subscriber from contact list | Bearer Token |

---

## 💡 Quick cURL Examples

### Register & Login
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "marketer@example.com", "password": "SecurePassword123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "marketer@example.com", "password": "SecurePassword123!"}'
```

### Create Contact List & Subscriber
```bash
# Create Contact List
curl -X POST http://localhost:8000/api/v1/contact-lists \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "VIP Customers", "description": "High value subscribers"}'

# Add Subscriber
curl -X POST http://localhost:8000/api/v1/contact-lists/<LIST_ID>/subscribers \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "status": "active",
    "metadata": {"source": "web_signup", "tier": "gold"}
  }'
```

---

## 🗺️ Project Roadmap

- [x] **Initialization** — Base FastAPI scaffolding, PostgreSQL, SQLAlchemy 2.x, Alembic, Docker, Redis, pytest, health checks.
- [x] **V1** — Audience Management (User Auth, ContactList CRUD, Subscriber CRUD, Ownership Isolation, JSON Metadata, Pagination, Constraints).
- [ ] **V2** — Campaign Engine
- [ ] **V3** — Celery + Redis Task Execution
- [ ] **V4** — Bulk CSV Data Management
- [ ] **V5** — Tracking + Webhooks
- [ ] **V6** — Campaign Scheduling
- [ ] **V7** — Unsubscribe + Compliance
- [ ] **V8** — Template Variables
- [ ] **V9** — Click Tracking
- [ ] **V10** — Analytics Dashboard Backend
- [ ] **V11** — High-Scale Campaign Engine
- [ ] **V12** — Rate Limiting
- [ ] **V13** — Multi-Provider Email Routing
- [ ] **V14** — Sender Domains
- [ ] **V15** — Multi-Tenancy + Billing
- [ ] **V16** — Audit Logging
- [ ] **V17** — Observability
- [ ] **V18** — Production Deployment
