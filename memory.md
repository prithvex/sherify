# Persistent Engineering Memory

## Project Status

- **Current Version**: V2 — Campaign Engine
- **Completed Versions**: Initialization, V1 (Audience Management), V2 (Campaign Engine)
- **Current Development Phase**: V2 Complete
- **Overall Health**: Healthy
- **V2 Status**: Completed

### Completed Work

- **Initialization**: FastAPI scaffolding, async SQLAlchemy 2.x, Alembic, Docker Compose, Redis, pytest async suite.
- **V1 (Audience Management)**:
  - User model & JWT authentication (`POST /auth/register`, `POST /auth/login`, `GET /users/me`).
  - ContactList CRUD (`/api/v1/contact-lists`).
  - Subscriber CRUD (`/api/v1/contact-lists/{list_id}/subscribers`) with scoped per-list email uniqueness.
  - Ownership protection & pagination/search conventions.
- **V2 (Campaign Engine)**:
  - `EmailTemplate` model, schema, repository, service, and CRUD endpoints (`/api/v1/templates`).
  - `EmailCampaign` model, schema, repository, service, and CRUD endpoints (`/api/v1/campaigns`).
  - Strict foreign resource ownership validation: creating/editing a campaign requires the user to own both the referenced template and contact list.
  - State machine: campaigns default to `DRAFT` upon creation.
  - Atomically validated `READY` transition via `POST /api/v1/campaigns/{id}/ready`.
  - Immutability of `READY` campaigns (attempts to PATCH a `READY` campaign return HTTP 400).
  - Referential integrity: deleting a template or contact list referenced by campaigns is safely rejected with HTTP 409 Conflict.
  - Migration `002_v2_campaign_engine` verified for complete upgrade/downgrade/upgrade cycle.
  - 69 automated tests (40 V1 tests + 29 V2 tests) passing with 100% success.

### Future Versions Not Implemented
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

## Database

### Domain Models
1. **`User`** (`users` table):
   - `id`: UUID (PK)
   - `email`: VARCHAR(255) (Unique, Indexed)
   - `password_hash`: VARCHAR(255)
   - `is_active`: BOOLEAN (Default True)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE
   - Relationships: `contact_lists` (cascade delete)

2. **`ContactList`** (`contact_lists` table):
   - `id`: UUID (PK)
   - `owner_id`: UUID (FK to `users.id` ON DELETE CASCADE, Indexed)
   - `name`: VARCHAR(255)
   - `description`: TEXT (Nullable)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE
   - Relationships: `owner` (`User`), `subscribers` (cascade delete)

3. **`Subscriber`** (`subscribers` table):
   - `id`: UUID (PK)
   - `contact_list_id`: UUID (FK to `contact_lists.id` ON DELETE CASCADE, Indexed)
   - `email`: VARCHAR(255) (Indexed)
   - `first_name`: VARCHAR(100) (Nullable)
   - `last_name`: VARCHAR(100) (Nullable)
   - `status`: VARCHAR(50) (Default 'active', Indexed)
   - `metadata`: JSON (Default '{}')
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE
   - Constraint: `UniqueConstraint("contact_list_id", "email")`

4. **`EmailTemplate`** (`email_templates` table):
   - `id`: UUID (PK)
   - `owner_id`: UUID (FK to `users.id` ON DELETE CASCADE, Indexed)
   - `name`: VARCHAR(255)
   - `subject`: VARCHAR(255)
   - `html_content`: TEXT
   - `text_content`: TEXT (Nullable)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE
   - Relationship: `owner` (`User`), `campaigns` (`EmailCampaign`)

5. **`EmailCampaign`** (`email_campaigns` table):
   - `id`: UUID (PK)
   - `owner_id`: UUID (FK to `users.id` ON DELETE CASCADE, Indexed)
   - `name`: VARCHAR(255)
   - `subject`: VARCHAR(255)
   - `template_id`: UUID (FK to `email_templates.id` ON DELETE RESTRICT, Indexed)
   - `contact_list_id`: UUID (FK to `contact_lists.id` ON DELETE RESTRICT, Indexed)
   - `status`: VARCHAR(50) (Default 'draft', Indexed)
   - `created_at`, `updated_at`: TIMESTAMP WITH TIME ZONE
   - Relationships: `owner` (`User`), `template` (`EmailTemplate`), `contact_list` (`ContactList`)

---

## API Endpoints

### Auth & Users
- `POST /api/v1/auth/register` — Register user.
- `POST /api/v1/auth/login` — Login & receive JWT.
- `GET /api/v1/users/me` — Current user profile.

### Contact Lists & Subscribers
- `POST /api/v1/contact-lists` — Create list.
- `GET /api/v1/contact-lists` — Paginated lists (`page`, `page_size`, `search`).
- `GET /api/v1/contact-lists/{list_id}` — Get single list.
- `PATCH /api/v1/contact-lists/{list_id}` — Update list.
- `DELETE /api/v1/contact-lists/{list_id}` — Delete list (blocked if referenced by campaign).
- `POST /api/v1/contact-lists/{list_id}/subscribers` — Create subscriber.
- `GET /api/v1/contact-lists/{list_id}/subscribers` — Paginated subscribers (`page`, `page_size`, `status`, `search`).
- `GET /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Get subscriber.
- `PATCH /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Update subscriber.
- `DELETE /api/v1/contact-lists/{list_id}/subscribers/{subscriber_id}` — Delete subscriber.

### Email Templates (V2)
- `POST /api/v1/templates` — Create template.
- `GET /api/v1/templates` — Paginated templates (`page`, `page_size`, `search`).
- `GET /api/v1/templates/{template_id}` — Get single template.
- `PATCH /api/v1/templates/{template_id}` — Update template.
- `DELETE /api/v1/templates/{template_id}` — Delete template (blocked if referenced by campaign).

### Email Campaigns (V2)
- `POST /api/v1/campaigns` — Create campaign (defaults to `DRAFT`).
- `GET /api/v1/campaigns` — Paginated campaigns (`page`, `page_size`, `status`, `search`).
- `GET /api/v1/campaigns/{campaign_id}` — Get single campaign.
- `PATCH /api/v1/campaigns/{campaign_id}` — Update campaign (allowed only for `DRAFT`).
- `DELETE /api/v1/campaigns/{campaign_id}` — Delete campaign.
- `POST /api/v1/campaigns/{campaign_id}/ready` — Transition `DRAFT` → `READY`.

### Health
- `GET /health` — Root health probe.
- `GET /api/v1/health` — V1 health probe.

---

## Architectural Decisions

1. **4-Tier Layered Architecture**: Maintained strict separation: Router → Service → Repository → Database.
2. **Campaign State Machine**: Functional states in V2 are strictly `DRAFT` and `READY`. Future states (`QUEUED`, `SENDING`, `COMPLETED`, `FAILED`, `CANCELLED`) are reserved in `CampaignStatus` enum.
3. **READY Campaigns Are Immutable**: Once a campaign reaches `READY`, normal `PATCH` operations are rejected with HTTP 400 to prevent silent invalidation before execution.
4. **Foreign Resource Ownership Validation**: Campaign creation and update methods verify that both `template_id` and `contact_list_id` belong to the authenticated `owner_id`.
5. **Referential Integrity on Deletion**: `template_id` and `contact_list_id` use `ON DELETE RESTRICT` at the DB level, and service layers return HTTP 409 Conflict if deletion is attempted while referenced by campaigns.
6. **No CampaignRecipient in V2**: Explicitly deferred to V3 where asynchronous campaign execution is introduced.
7. **No Email Sending in V2**: Campaign engine only manages templates, campaigns, and draft/ready state preparation.

---

## Known Issues

- None.

---

## Current Work

- None.

---

## Next

- **V3 — Celery + Redis Campaign Execution**:
  - Introduce `CampaignRecipient` model to capture recipient snapshots.
  - Implement Celery worker tasks consuming from Redis to dispatch campaign batches asynchronously.
