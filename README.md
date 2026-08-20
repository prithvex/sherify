# Automated Mass Campaign Manager (Sherify)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org)
[![Alembic](https://img.shields.io/badge/Alembic-1.13+-orange.svg)](https://alembic.sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com)

> **Current Implementation Status**: **V2 — Campaign Engine Completed.**

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
│ (Business logic, ownership validation, JWT & state)    │
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
│   ├── versions/               # Migration version files (001_initial_v1, 002_v2_campaign_engine)
│   ├── env.py                  # Alembic environment runner
│   └── script.py.mako          # Migration template
├── app/                        # Application core package
│   ├── api/                    # API router layer
│   │   ├── v1/                 # API Version 1
│   │   │   ├── endpoints/      # Specific endpoints (auth, users, contact_lists, templates, campaigns, health)
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
│   │   ├── subscriber.py       # Subscriber entity with per-list uniqueness
│   │   ├── template.py         # EmailTemplate entity
│   │   └── campaign.py         # EmailCampaign entity
│   ├── repositories/           # Data access repository layer
│   │   ├── user_repo.py        # User queries
│   │   ├── contact_list_repo.py# ContactList queries & pagination
│   │   ├── subscriber_repo.py  # Subscriber queries & pagination
│   │   ├── template_repo.py    # EmailTemplate queries & referential checks
│   │   └── campaign_repo.py    # EmailCampaign queries & referential checks
│   ├── schemas/                # Pydantic validation models & DTOs
│   │   ├── common.py           # Pagination schemas (PaginatedResponse, PaginationParams)
│   │   ├── user.py             # User DTOs (Register, Login, Token, Response)
│   │   ├── contact_list.py     # ContactList DTOs (Create, Update, Response)
│   │   ├── subscriber.py       # Subscriber DTOs (Create, Update, Response, Status Enum)
│   │   ├── template.py         # EmailTemplate DTOs (Create, Update, Response)
│   │   ├── campaign.py         # EmailCampaign DTOs (Create, Update, Response, Status Enum)
│   │   └── health.py           # Health check response schemas
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py     # Authentication & registration
│   │   ├── contact_list_service.py # ContactList business logic
│   │   ├── subscriber_service.py   # Subscriber business logic
│   │   ├── template_service.py # EmailTemplate business logic
│   │   └── campaign_service.py # EmailCampaign business logic & state validation
│   └── main.py                 # FastAPI application, lifespan, CORS, and root health check
├── tests/                      # Pytest async test suite (69 passing tests)
│   ├── conftest.py             # Fixtures, test database lifecycle, test client
│   ├── test_auth.py            # Registration, login, password security tests
│   ├── test_users.py           # Profile & token authorization tests
│   ├── test_contact_lists.py   # Contact list CRUD & cross-user isolation tests
│   ├── test_subscribers.py     # Subscriber CRUD, per-list uniqueness & filter tests
│   ├── test_templates.py       # Template CRUD, search, pagination, validation tests
│   ├── test_campaigns.py       # Campaign CRUD, ownership, DRAFT rules, immutability tests
│   ├── test_campaign_ready.py  # Campaign DRAFT -> READY validation state tests
│   ├── test_referential_integrity.py # Template & ContactList deletion protection tests
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
```

### 4. Database Migrations
Apply database migrations using Alembic:
```bash
# Apply all migrations
alembic upgrade head

# Rollback last migration (if needed)
alembic downgrade -1
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

The repository features comprehensive integration and unit tests covering authentication, authorization, ownership isolation, pagination, filters, state transitions, and database constraints.

Run the complete test suite:
```bash
pytest -v
```

---

## 📡 API Reference

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
| `DELETE` | `/api/v1/contact-lists/{list_id}` | Delete contact list (blocked if referenced by campaign) | Bearer Token |

### 3. Subscribers (Nested under Contact Lists)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contact-lists/{list_id}/subscribers` | Add subscriber to contact list | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers` | List subscribers (paginated, filtered) | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Get subscriber by ID | Bearer Token |
| `PATCH` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Update subscriber details | Bearer Token |
| `DELETE` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Remove subscriber from contact list | Bearer Token |

### 4. Email Templates (V2)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/templates` | Create a new email template | Bearer Token |
| `GET` | `/api/v1/templates` | List user's email templates (paginated, search) | Bearer Token |
| `GET` | `/api/v1/templates/{template_id}` | Get single email template by ID | Bearer Token |
| `PATCH` | `/api/v1/templates/{template_id}` | Update email template details | Bearer Token |
| `DELETE` | `/api/v1/templates/{template_id}` | Delete email template (blocked if referenced by campaign) | Bearer Token |

### 5. Email Campaigns (V2)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/campaigns` | Create campaign (defaults to `DRAFT`) | Bearer Token |
| `GET` | `/api/v1/campaigns` | List campaigns (paginated, status & search filter) | Bearer Token |
| `GET` | `/api/v1/campaigns/{campaign_id}` | Get single campaign by ID | Bearer Token |
| `PATCH` | `/api/v1/campaigns/{campaign_id}` | Update campaign (allowed only for `DRAFT`) | Bearer Token |
| `DELETE` | `/api/v1/campaigns/{campaign_id}` | Delete campaign | Bearer Token |
| `POST` | `/api/v1/campaigns/{campaign_id}/ready` | Validate and transition `DRAFT` → `READY` | Bearer Token |

---

## 💡 Quick cURL Examples

### Create Template
```bash
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Newsletter",
    "subject": "Summer is here!",
    "html_content": "<h1>Hello</h1><p>Check out our summer lineup!</p>",
    "text_content": "Hello! Check out our summer lineup!"
  }'
```

### Create Campaign & Transition to READY
```bash
# 1. Create Campaign in DRAFT status
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Launch",
    "subject": "Summer is here!",
    "template_id": "<TEMPLATE_ID>",
    "contact_list_id": "<LIST_ID>"
  }'

# 2. Transition Campaign to READY status
curl -X POST http://localhost:8000/api/v1/campaigns/<CAMPAIGN_ID>/ready \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 🗺️ Project Roadmap

- [x] **Initialization** — Base FastAPI scaffolding, PostgreSQL, SQLAlchemy 2.x, Alembic, Docker, Redis, pytest, health checks.
- [x] **V1** — Audience Management (User Auth, ContactList CRUD, Subscriber CRUD, Ownership Isolation, JSON Metadata, Pagination, Constraints).
- [x] **V2** — Campaign Engine (EmailTemplate CRUD, EmailCampaign CRUD, DRAFT status, READY transition validation, Referential Integrity, Immutability).
- [ ] **V3** — Celery + Redis Task Execution & CampaignRecipient
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
