# Persistent Engineering Memory

## Project Status

- **Current Version**: V1 — Audience Management
- **Completed Versions**: Initialization, V1 (Audience Management)
- **Current Development Phase**: V1 Complete
- **Overall Health**: Healthy
- **V1 Status**: Completed

### V1 Completed Features
- **User Authentication & Authorization**:
  - `POST /api/v1/auth/register` — User registration with email uniqueness and bcrypt password hashing.
  - `POST /api/v1/auth/login` — JWT token generation with expiration.
  - `GET /api/v1/users/me` — Authenticated profile access with active status validation.
  - Ownership protection via `get_current_user` and `get_current_active_user` dependencies.
- **ContactList Management**:
  - Full CRUD (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`) on `/api/v1/contact-lists`.
  - Pagination (`page`, `page_size`) and keyword search filtering (`search`).
  - Strict ownership isolation: users cannot view, edit, or delete lists belonging to others.
- **Subscriber Management**:
  - Full CRUD (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`) on `/api/v1/contact-lists/{list_id}/subscribers`.
  - Pagination, status filtering (`status`), and keyword search (`search`).
  - Per-contact-list email uniqueness: subscribers cannot have duplicate emails in the same list, but can exist in multiple different lists.
  - JSON metadata support for dynamic custom attributes.
  - Strict list and subscriber ownership verification.
- **Database & Persistence**:
  - PostgreSQL 16 persistence via async SQLAlchemy 2.x and `asyncpg`.
  - UUID primary keys, foreign keys with `ON DELETE CASCADE`, composite indexes.
  - Alembic migration `001_initial_v1` verified for complete upgrade/downgrade/upgrade cycle.
- **Testing**:
  - 40 passing tests covering unit, integration, authentication, authorization, ownership isolation, pagination, filters, and DB constraints.
- **Docker**:
  - Docker Compose orchestration with `api`, `postgres:16-alpine`, and `redis:7-alpine`.

### Future Versions Not Implemented
- Campaigns & Engine (V2)
- Celery & Redis Task Processing (V3)
- CSV Ingestion (V4)
- Tracking & Webhooks (V5)
- Scheduling (V6)
- Compliance & Unsubscribe (V7)
- Template Variables (V8)
- Click Tracking (V9)
- Analytics Dashboard (V10)
- High-Scale Engine (V11)
- Rate Limiting (V12)
- Multi-Provider Email Routing (V13)
- Sender Domains (V14)
- Multi-Tenancy & Billing (V15)
- Audit Logging (V16)
- Observability (V17)
- Production Deployment (V18)

---

## Architecture

- **Pattern**: 4-Tier Layered (Router → Service → Repository → Database).
- **Backend**: Python 3.10+, FastAPI (Async).
- **Database**: PostgreSQL 16.
- **ORM**: SQLAlchemy 2.x (Async with `asyncpg`).
- **Authentication**: JWT Bearer Tokens (`PyJWT`) with salted `bcrypt` password hashing.
- **Queue**: Redis 7 (Infrastructure container ready; Celery tasks introduced in V3).
- **Cache**: Redis 7.
- **Deployment**: Docker & Docker Compose.

---

## Project Structure

```
sherify/
├── alembic/                # Async database migration scripts
│   ├── versions/           # Migration versions (001_initial_v1_audience_management.py)
│   ├── env.py              # Async migration runner loading Base.metadata
│   └── script.py.mako      # Migration file template
├── app/                    # Core application package
│   ├── api/                # API router layer
│   │   ├── v1/             # API version 1 endpoints
│   │   │   ├── endpoints/  # Health, auth, users, contact_lists
│   │   │   └── api.py      # Router aggregation for v1
│   │   └── deps.py         # Dependencies (get_db, get_current_user, get_current_active_user)
│   ├── core/               # App configuration & core components
│   │   ├── config.py       # Pydantic v2 BaseSettings
│   │   ├── database.py     # SQLAlchemy 2.x async engine, sessionmaker, get_db
│   │   └── security.py     # Password hashing & JWT encode/decode
│   ├── models/             # Database models
│   │   ├── base.py         # DeclarativeBase, UUIDMixin, TimestampMixin
│   │   ├── user.py         # User model
│   │   ├── contact_list.py # ContactList model
│   │   └── subscriber.py   # Subscriber model
│   ├── repositories/       # Data access layer
│   │   ├── user_repo.py    # User repository
│   │   ├── contact_list_repo.py # ContactList repository
│   │   └── subscriber_repo.py   # Subscriber repository
│   ├── schemas/            # Pydantic schemas / DTOs
│   │   ├── common.py       # Pagination schemas
│   │   ├── user.py         # User DTOs
│   │   ├── contact_list.py # ContactList DTOs
│   │   ├── subscriber.py   # Subscriber DTOs
│   │   └── health.py       # Health check response schemas
│   ├── services/           # Business logic layer
│   │   ├── auth_service.py # Authentication & registration
│   │   ├── contact_list_service.py # ContactList business logic
│   │   └── subscriber_service.py   # Subscriber business logic
│   └── main.py             # FastAPI entrypoint, lifespan, CORS, and root routes
├── tests/                  # Pytest test suite (40 passing tests)
│   ├── conftest.py         # Test fixtures, test engine, async HTTP client
│   ├── test_auth.py        # Registration, login, password security tests
│   ├── test_users.py       # User profile and token verification tests
│   ├── test_contact_lists.py # Contact list CRUD and isolation tests
│   ├── test_subscribers.py # Subscriber CRUD and uniqueness tests
│   ├── test_database_constraints.py # Cascade and DB constraint tests
│   └── test_health.py      # Health check and startup tests
├── .dockerignore           # Files excluded from Docker builds
├── .env.example            # Sample environment variables
├── .gitignore              # Files excluded from git
├── alembic.ini             # Alembic migration configuration
├── docker-compose.yml      # Multi-container local orchestration (API, Postgres, Redis)
├── Dockerfile              # Container definition for FastAPI application
├── memory.md               # Persistent engineering memory
├── pyproject.toml          # Build configuration and pytest options
├── README.md               # Project overview and developer guide
└── requirements.txt        # Minimal async-first application dependencies
```

---

## Database

### Domain Models
1. **`User`** (`users` table):
   - `id`: UUID (PK, Indexed)
   - `email`: VARCHAR(255) (Unique, Indexed, Non-null)
   - `password_hash`: VARCHAR(255) (Non-null)
   - `is_active`: BOOLEAN (Default True, Non-null)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE (Non-null)
   - Relationship: `contact_lists` (cascade delete)

2. **`ContactList`** (`contact_lists` table):
   - `id`: UUID (PK, Indexed)
   - `owner_id`: UUID (FK to `users.id` ON DELETE CASCADE, Indexed, Non-null)
   - `name`: VARCHAR(255) (Non-null)
   - `description`: TEXT (Nullable)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE (Non-null)
   - Relationship: `owner` (`User`), `subscribers` (cascade delete)

3. **`Subscriber`** (`subscribers` table):
   - `id`: UUID (PK, Indexed)
   - `contact_list_id`: UUID (FK to `contact_lists.id` ON DELETE CASCADE, Indexed, Non-null)
   - `email`: VARCHAR(255) (Indexed, Non-null)
   - `first_name`: VARCHAR(100) (Nullable)
   - `last_name`: VARCHAR(100) (Nullable)
   - `status`: VARCHAR(50) (Default 'active', Indexed, Non-null)
   - `metadata`: JSON (Default '{}', Non-null)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE (Non-null)
   - **Constraints**:
     - `UniqueConstraint("contact_list_id", "email", name="uq_subscriber_contact_list_email")`
     - Index: `("contact_list_id", "status")`

---

## API Endpoints (V1)

### Auth & Users
- `POST /api/v1/auth/register` — Register user.
- `POST /api/v1/auth/login` — Login & receive JWT.
- `GET /api/v1/users/me` — Current user profile.

### Contact Lists
- `POST /api/v1/contact-lists` — Create list.
- `GET /api/v1/contact-lists` — Paginated lists with `page`, `page_size`, `search`.
- `GET /api/v1/contact-lists/{list_id}` — Get single list.
- `PATCH /api/v1/contact-lists/{list_id}` — Update list.
- `DELETE /api/v1/contact-lists/{list_id}` — Delete list.

### Subscribers
- `POST /api/v1/contact-lists/{list_id}/subscribers` — Create subscriber.
- `GET /api/v1/contact-lists/{list_id}/subscribers` — Paginated subscribers with `page`, `page_size`, `status`, `search`.
- `GET /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Get single subscriber.
- `PATCH /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Update subscriber.
- `DELETE /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Delete subscriber.

### Health
- `GET /health` — Root health probe.
- `GET /api/v1/health` — V1 health probe.

---

## Architectural Decisions

1. **4-Tier Architecture**: Router → Service → Repository → Database. Thin route handlers, all business rules and ownership checks inside services, SQL queries encapsulated in repositories.
2. **Per-List Subscriber Uniqueness**: Subscriber email is constrained unique per `contact_list_id` rather than globally, enabling users to maintain multi-list subscriptions.
3. **Strict Ownership Isolation**: Service methods query lists by both `list_id` and `owner_id`. Unauthorized cross-user requests return 404 to prevent enumeration and access.
4. **PostgreSQL Parity & NullPool in Tests**: Unit/integration tests use `NullPool` to prevent connection leaks across async test loops while running directly against PostgreSQL.
5. **No Premature Celery Integration**: Kept queue infrastructure cleanly in Redis without premature Celery workers before V3.

---

## Do Not Break

- Do not bypass ownership verification when querying ContactLists or Subscribers.
- Do not make subscriber email globally unique across contact lists.
- Do not introduce synchronous database drivers or blocking queries into async endpoints.
- Do not put business logic or direct database queries in route handlers.
- Maintain Pydantic v2 and SQLAlchemy 2.x idioms.
- Always update `memory.md` when models, migrations, endpoints, or configurations change.
