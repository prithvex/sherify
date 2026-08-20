# Automated Mass Campaign Manager (Sherify)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue.svg)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5-purple.svg)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3+-green.svg)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com)

> **Current Implementation Status**: **Frontend V1 + Backend V1–V5 Completed.**

---

## 📖 Project Purpose

The **Automated Mass Campaign Manager** is a high-scale, production-oriented email campaign platform engineered to manage audiences, ingest large subscriber datasets via streaming CSV imports, compose reusable templates with safe live preview, execute high-volume campaigns asynchronously with Celery/Redis, track email opens via tracking pixels, ingest delivery/bounce provider webhooks, and visualize durable SQL-aggregated analytics in a sleek SaaS dashboard.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│             Frontend SPA (React 18 + TS + Vite)         │
│   (Dashboard, Audiences, CSV Import, Templates, Stats) │
└───────────────────────────┬────────────────────────────┘
                            │ (REST HTTP / JWT Bearer)
┌───────────────────────────▼────────────────────────────┐
│               Backend API (FastAPI)                    │
│   (Routers, Pydantic DTOs, Security, State Machine)    │
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
├── alembic/                    # Async database migration scripts (001-005)
├── app/                        # FastAPI Backend core package
│   ├── api/                    # API router layer (auth, users, contact_lists, templates, campaigns, imports, webhooks, tracking)
│   ├── core/                   # Config, database engine, password hashing, JWT
│   ├── models/                 # SQLAlchemy models (User, ContactList, Subscriber, Template, Campaign, Recipient, Import, Tracking)
│   ├── providers/              # Email provider abstraction (MockEmailProvider)
│   ├── webhooks/               # Webhook verifiers & parsers (MockWebhookVerifier/Parser)
│   ├── storage/                # File storage abstraction (LocalFileStorage)
│   ├── repositories/           # Data access repository layer
│   ├── schemas/                # Pydantic validation models & DTOs
│   ├── services/               # Business logic layer
│   ├── tasks/                  # Celery background tasks (campaigns, imports, webhooks)
│   └── main.py                 # FastAPI application root & tracking pixel route
├── frontend/                   # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── api/                # Centralized Axios client & services
│   │   ├── components/         # Layout (Sidebar, Header) & Common (Button, Input, Select, Modal, Badge, SafeHtmlPreview)
│   │   ├── context/            # AuthContext (token storage, login/logout, user state)
│   │   ├── pages/              # Dashboard, Contacts, Templates, Campaigns, Analytics, Settings
│   │   ├── types/              # TypeScript definitions matching backend
│   │   └── test/               # Vitest unit test suites
│   ├── Dockerfile              # Multi-stage production Nginx container
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/                      # Pytest backend async test suite (108 tests)
├── docker-compose.yml          # Full-stack orchestration (API, Worker, Frontend, PostgreSQL, Redis)
├── memory.md                   # Engineering memory & version status tracker
└── README.md                   # System documentation
```

---

## 🚀 Getting Started

### 1. Run Complete Stack with Docker Compose
```bash
docker compose up --build -d
```
Services will be live at:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Local Development Setup

#### Backend Setup:
```bash
# Setup virtual environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000

# Start Celery Worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Accessible at [http://localhost:3000](http://localhost:3000).

---

## 🧪 Testing

### Backend Test Suite (108 Tests):
```bash
pytest -v
```

### Frontend Test Suite (9 Tests):
```bash
cd frontend
npm test
```

### Frontend Typecheck & Production Build:
```bash
cd frontend
npm run typecheck
npm run build
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
- [x] **Frontend V1** — Complete React + TypeScript + Vite Campaign Manager Dashboard UI.
- [ ] **V6** — Campaign Scheduling
- [ ] **V7** — Unsubscribe + Compliance
- [ ] **V8** — Template Variables
- [ ] **V9** — Click Tracking
- [ ] **V10** — Analytics Dashboard Backend
