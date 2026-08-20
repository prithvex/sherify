# Automated Mass Campaign Manager (Sherify)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org)
[![Celery](https://img.shields.io/badge/Celery-5.3+-green.svg)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Alembic](https://img.shields.io/badge/Alembic-1.13+-orange.svg)](https://alembic.sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com)

> **Current Implementation Status**: **V5 — Tracking & Webhooks Completed.**

---

## 📖 Project Purpose

The **Automated Mass Campaign Manager** is a high-scale, production-oriented email campaign system engineered to manage audiences, ingest large subscriber datasets via streaming CSV imports, execute high-volume campaigns asynchronously, track email engagement and bounces, and provide aggregated campaign performance statistics.

---

## 🏛️ Architecture & Design Pattern

The system strictly enforces a 4-tier layered architecture with asynchronous background execution:

```
┌────────────────────────────────────────────────────────┐
│                   Router Layer                         │
│   (HTTP parsing, Pydantic DTOs, dependency injection)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Service Layer                        │
│ (Business logic, ownership validation, JWT & state)    │
└─────────────────────┬──────────────┬───────────────────┘
                      │              │ (Enqueue Tasks)
                      │              ▼
                      │       ┌──────────────┐
                      │       │ Redis Broker │
                      │       └──────┬───────┘
                      │              │
                      │       ┌──────▼───────┐
                      │       │ Celery Worker│
                      │       │  (Batching)  │
                      │       └──────┬───────┘
                      │              │ (Dispatch / Parse)
                      │       ┌──────▼───────┐
                      │       │Storage/Email │
                      │       └──────┬───────┘
┌─────────────────────▼──────────────▼───────────────────┐
│                  Repository Layer                      │
│     (Async queries, pagination, DB filter logic)       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Database Layer                        │
│ (PostgreSQL 16, UUIDs, Foreign Keys, Snapshot History) │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
sherify/
├── alembic/                    # Async database migration scripts
│   ├── versions/               # Migration version files (001_initial_v1, 002_v2, 003_v3, 004_v4, 005_v5)
│   ├── env.py                  # Alembic environment runner
│   └── script.py.mako          # Migration template
├── app/                        # Application core package
│   ├── api/                    # API router layer
│   │   ├── v1/                 # API Version 1
│   │   │   ├── endpoints/      # Endpoints (auth, users, contact_lists, templates, campaigns, imports, webhooks, tracking, health)
│   │   │   └── api.py          # V1 router aggregation
│   │   └── deps.py             # FastAPI dependencies (get_db, get_current_user, get_current_active_user)
│   ├── core/                   # Core application configuration & security
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # Async SQLAlchemy engine & sessionmaker (NullPool for event-loop safety)
│   │   └── security.py         # Password hashing (bcrypt) & JWT helpers
│   ├── models/                 # SQLAlchemy 2.x declarative models
│   │   ├── base.py             # Base model, UUIDMixin, TimestampMixin
│   │   ├── user.py             # User entity
│   │   ├── contact_list.py     # ContactList entity
│   │   ├── subscriber.py       # Subscriber entity with per-list uniqueness
│   │   ├── template.py         # EmailTemplate entity
│   │   ├── campaign.py         # EmailCampaign entity
│   │   ├── recipient.py        # CampaignRecipient snapshot entity (tracking fields added in V5)
│   │   ├── import_job.py       # ImportJob and ImportError entities (V4)
│   │   └── tracking.py         # TrackingEvent and WebhookEvent entities (V5)
│   ├── providers/              # Email provider abstraction (V3)
│   │   ├── base.py             # BaseEmailProvider ABC & dataclasses
│   │   ├── mock.py             # MockEmailProvider with test failure hooks
│   │   └── __init__.py         # Provider factory (get_email_provider)
│   ├── webhooks/               # Webhook verification & parsing abstraction (V5)
│   │   ├── base.py             # BaseWebhookVerifier & BaseWebhookParser ABCs
│   │   ├── mock.py             # MockWebhookVerifier & MockWebhookParser
│   │   └── __init__.py         # Webhook provider factory
│   ├── storage/                # File storage abstraction (V4)
│   │   ├── base.py             # BaseFileStorage ABC
│   │   ├── local.py            # LocalFileStorage implementation
│   │   └── __init__.py         # Storage factory (get_file_storage)
│   ├── repositories/           # Data access repository layer
│   │   ├── user_repo.py        # User queries
│   │   ├── contact_list_repo.py# ContactList queries & pagination
│   │   ├── subscriber_repo.py  # Subscriber queries, pagination & streaming
│   │   ├── template_repo.py    # EmailTemplate queries & referential checks
│   │   ├── campaign_repo.py    # EmailCampaign queries & referential checks
│   │   ├── recipient_repo.py   # CampaignRecipient batching, tracking & SQL aggregation
│   │   ├── tracking_repo.py    # TrackingEvent and WebhookEvent queries (V5)
│   │   ├── import_job_repo.py  # ImportJob queries (V4)
│   │   └── import_error_repo.py# ImportError queries (V4)
│   ├── schemas/                # Pydantic validation models & DTOs
│   │   ├── common.py           # Pagination schemas (PaginatedResponse, PaginationParams)
│   │   ├── user.py             # User DTOs (Register, Login, Token, Response)
│   │   ├── contact_list.py     # ContactList DTOs (Create, Update, Response)
│   │   ├── subscriber.py       # Subscriber DTOs (Create, Update, Response, Status Enum)
│   │   ├── template.py         # EmailTemplate DTOs (Create, Update, Response)
│   │   ├── campaign.py         # EmailCampaign DTOs (Create, Update, Response, SendResponse, Status Enum)
│   │   ├── recipient.py        # CampaignRecipient DTOs (Response, Status Enum)
│   │   ├── import_job.py       # ImportJob & ImportError DTOs (V4)
│   │   ├── tracking.py         # TrackingEvent, WebhookEvent & CampaignStats DTOs (V5)
│   │   └── health.py           # Health check response schemas
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py     # Authentication & registration
│   │   ├── contact_list_service.py # ContactList business logic
│   │   ├── subscriber_service.py   # Subscriber business logic
│   │   ├── template_service.py # EmailTemplate business logic
│   │   ├── campaign_service.py # EmailCampaign business logic & state validation
│   │   ├── campaign_execution_service.py # Worker batch campaign execution with tracking pixel injection (V3+V5)
│   │   ├── tracking_service.py # Email open tracking service (V5)
│   │   ├── webhook_service.py  # Webhook signature verification and ingestion (V5)
│   │   ├── webhook_execution_service.py # Asynchronous webhook bounce/delivery processing (V5)
│   │   ├── import_service.py   # Import job dispatch & ownership validation (V4)
│   │   └── import_execution_service.py # CSV streaming & batch ingestion engine (V4)
│   ├── tasks/                  # Celery background tasks
│   │   ├── celery_app.py       # Celery application configuration
│   │   ├── campaign_tasks.py   # execute_campaign_task definition & backoff retry (V3)
│   │   ├── import_tasks.py     # process_subscriber_import definition & backoff retry (V4)
│   │   ├── webhook_tasks.py    # process_webhook_event definition & backoff retry (V5)
│   │   └── __init__.py         # Task exports
│   └── main.py                 # FastAPI application, lifespan, CORS, /track route, and health check
├── tests/                      # Pytest async test suite (108 passing tests)
│   ├── conftest.py             # Fixtures, test database lifecycle, test client
│   ├── test_auth.py            # Registration, login, password security tests
│   ├── test_users.py           # Profile & token authorization tests
│   ├── test_contact_lists.py   # Contact list CRUD & cross-user isolation tests
│   ├── test_subscribers.py     # Subscriber CRUD, per-list uniqueness & filter tests
│   ├── test_templates.py       # Template CRUD, search, pagination, validation tests
│   ├── test_campaigns.py       # Campaign CRUD, ownership, DRAFT rules, immutability tests
│   ├── test_campaign_ready.py  # Campaign DRAFT -> READY validation state tests
│   ├── test_campaign_send.py   # Send endpoint, 202 status, duplicate send protection (V3)
│   ├── test_campaign_execution.py # Worker execution scenarios, crash recovery, snapshot tests (V3)
│   ├── test_csv_import_api.py  # CSV upload endpoint, 202 status, job status & error querying (V4)
│   ├── test_csv_import_execution.py # Streaming CSV parser, edge-case headers, duplicate handling (V4)
│   ├── test_tracking_open.py   # Open tracking pixel, 1x1 transparent GIF, idempotency tests (V5)
│   ├── test_webhooks.py        # Webhook signature verification, deduplication, bounce handling (V5)
│   ├── test_campaign_stats.py  # SQL-aggregated stats, open rate, bounce rate, zero safety (V5)
│   ├── test_referential_integrity.py # Template & ContactList deletion protection tests
│   ├── test_database_constraints.py # Cascade deletion & FK integrity tests
│   └── test_health.py          # System health check tests
├── .env.example                # Example environment variables
├── alembic.ini                 # Alembic configuration
├── docker-compose.yml          # Multi-container orchestration (API, Worker, PostgreSQL, Redis)
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
# Terminal 1: Start API server
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Celery worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```
Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🐳 Docker Setup

To run the complete production-like stack using Docker Compose:

```bash
# Start all containers in background (API, Worker, PostgreSQL, Redis)
docker compose up --build -d

# View container status
docker compose ps

# View real-time worker logs
docker compose logs -f worker
```

The stack includes:
- `api` — FastAPI application on port `8000`
- `worker` — Celery worker executing campaign, import, and webhook tasks
- `postgres` — PostgreSQL 16 database with health check
- `redis` — Redis 7 cache & Celery broker with health check

---

## 🧪 Testing

The repository features **108 comprehensive integration and unit tests** covering authentication, authorization, ownership isolation, pagination, filters, state transitions, async batch campaign execution, streaming CSV import ingestion, open tracking pixels, webhook verification, bounce handling, campaign stats calculation, and database constraints.

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

### 3. Subscribers & Bulk CSV Ingestion (V1 + V4)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/contact-lists/{list_id}/subscribers` | Add individual subscriber to contact list | Bearer Token |
| `POST` | `/api/v1/contact-lists/{list_id}/subscribers/import` | Upload CSV file for asynchronous batch ingestion (`HTTP 202 Accepted`) | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers` | List subscribers (paginated, filtered) | Bearer Token |
| `GET` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Get subscriber by ID | Bearer Token |
| `PATCH` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Update subscriber details | Bearer Token |
| `DELETE` | `/api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` | Remove subscriber from contact list | Bearer Token |

### 4. Bulk Import Job Status & Errors (V4)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/imports/{import_job_id}` | Retrieve import status, total/imported/duplicate/invalid counts | Bearer Token |
| `GET` | `/api/v1/imports/{import_job_id}/errors` | Retrieve paginated row-level validation errors for an import | Bearer Token |

### 5. Email Templates (V2)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/templates` | Create a new email template | Bearer Token |
| `GET` | `/api/v1/templates` | List user's email templates (paginated, search) | Bearer Token |
| `GET` | `/api/v1/templates/{template_id}` | Get single email template by ID | Bearer Token |
| `PATCH` | `/api/v1/templates/{template_id}` | Update email template details | Bearer Token |
| `DELETE` | `/api/v1/templates/{template_id}` | Delete email template (blocked if referenced by campaign) | Bearer Token |

### 6. Email Campaigns & Asynchronous Execution (V2 + V3)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/campaigns` | Create campaign (defaults to `DRAFT`) | Bearer Token |
| `GET` | `/api/v1/campaigns` | List campaigns (paginated, status & search filter) | Bearer Token |
| `GET` | `/api/v1/campaigns/{campaign_id}` | Get single campaign by ID | Bearer Token |
| `PATCH` | `/api/v1/campaigns/{campaign_id}` | Update campaign (allowed only for `DRAFT`) | Bearer Token |
| `DELETE` | `/api/v1/campaigns/{campaign_id}` | Delete campaign | Bearer Token |
| `POST` | `/api/v1/campaigns/{campaign_id}/ready` | Validate and transition `DRAFT` → `READY` | Bearer Token |
| `POST` | `/api/v1/campaigns/{campaign_id}/send` | Snapshot recipients, transition `READY` → `QUEUED`, and enqueue background execution (`HTTP 202 Accepted`) | Bearer Token |
| `GET` | `/api/v1/campaigns/{campaign_id}/stats` | Retrieve SQL-aggregated delivery and engagement statistics (sent, failed, bounced, opened, rates) | Bearer Token |

### 7. Tracking & Webhooks (V5)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/track/open/{tracking_token}` | Public tracking pixel endpoint returning 1x1 transparent GIF (`image/gif`) | Public (No Auth) |
| `POST` | `/api/v1/webhooks/email/{provider}` | Public email provider webhook receiver (`HTTP 202 Accepted`) | Provider Signature |

---

## 🗺️ Project Roadmap

- [x] **Initialization** — Base FastAPI scaffolding, PostgreSQL, SQLAlchemy 2.x, Alembic, Docker, Redis, pytest, health checks.
- [x] **V1** — Audience Management (User Auth, ContactList CRUD, Subscriber CRUD, Ownership Isolation, JSON Metadata, Pagination, Constraints).
- [x] **V2** — Campaign Engine (EmailTemplate CRUD, EmailCampaign CRUD, DRAFT status, READY transition validation, Referential Integrity, Immutability).
- [x] **V3** — Celery + Redis Task Execution & CampaignRecipient (Asynchronous execution, snapshot records, batching, idempotency, mock email provider, retries).
- [x] **V4** — Bulk CSV Data Management (Asynchronous CSV ingestion, streaming parser, batch inserts, duplicate handling, import error logs).
- [x] **V5** — Tracking & Webhooks (Open tracking pixels, provider webhook signature verification, async bounce handling, recipient history, campaign stats).
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
