# Persistent Engineering Memory

## Project Status

- **Current Version**: V6 — Production Email Delivery & Campaign Scheduling
- **Completed Versions**: Initialization, V1 (Audience Management), V2 (Campaign Engine), V3 (Campaign Execution), V4 (Bulk Data Management), V5 (Tracking & Webhooks), Frontend V1 (Complete UI Dashboard), V6 (Production Delivery & Scheduling)
- **Current Development Phase**: V6 Complete
- **Overall Health**: Healthy
- **V6 Status**: Completed

### Completed Work

- **Initialization**: FastAPI scaffolding, async SQLAlchemy 2.x, Alembic, Docker Compose, Redis, pytest async suite.
- **V1 (Audience Management)**: User model, JWT auth, ContactList CRUD, Subscriber CRUD with scoped per-list uniqueness.
- **V2 (Campaign Engine)**: EmailTemplate CRUD, EmailCampaign CRUD, DRAFT status, READY transition validation, foreign resource ownership validation, immutability of READY campaigns, referential integrity protection on template and contact list deletion.
- **V3 (Campaign Execution)**: `CampaignRecipient` snapshot model, Celery background worker setup with Redis broker (`execute_campaign_task`), `BaseEmailProvider` abstraction, `MockEmailProvider`, batch campaign delivery engine, idempotent retries, `POST /campaigns/{id}/send` returning `HTTP 202 Accepted`.
- **V4 (Bulk Data Management)**: `ImportJob` and `ImportError` models, `LocalFileStorage` streaming chunk writes and cleanup, `process_subscriber_import` Celery task, batch database insertion (`IMPORT_BATCH_SIZE=500`), error capturing, and endpoints (`POST /contact-lists/{id}/subscribers/import`, `GET /imports/{id}`, `GET /imports/{id}/errors`).
- **V5 (Tracking & Webhooks)**:
  - **Open Tracking**: Cryptographically secure URL-safe `tracking_token` per recipient, public `GET /track/open/{tracking_token}` returning 1x1 transparent GIF (`image/gif`) with cache-busting headers, tracking pixel injection into HTML emails during dispatch, idempotent first-open recording setting `CampaignRecipient.opened_at` and creating `TrackingEvent(event_type="opened")`.
  - **Provider Webhooks**: Public `POST /api/v1/webhooks/email/{provider}` endpoint returning `HTTP 202 Accepted`, pluggable `BaseWebhookVerifier` and `BaseWebhookParser` abstractions with HMAC verification, normalized internal `NormalizedWebhookEvent` data structures, `WebhookEvent` model with unique constraint on `(provider, provider_event_id)` ensuring deduplication.
  - **Asynchronous Webhook Processing & Bounce Handling**: Celery task `process_webhook_event`, `WebhookExecutionService` resolving recipient by `provider_message_id`, updating delivery status to `bounced` (from `sent`), recording `CampaignRecipient.bounced_at` while preserving `sent_at`, and recording immutable `TrackingEvent(event_type="bounced")`.
  - **Campaign Statistics**: Database SQL-aggregated endpoint `GET /api/v1/campaigns/{campaign_id}/stats` calculating `total_recipients`, `sent_count`, `failed_count`, `bounced_count`, `opened_count`, `open_rate` (`opened / sent`), and `bounce_rate` (`bounced / sent`), with division-by-zero protection.
- **Frontend V1 (Complete Campaign Manager UI)**:
  - Built production-grade React 18 + TypeScript + Vite SPA.
  - State management & server caching using TanStack Query v5.
  - Centralized Axios client with JWT bearer token interceptor and automatic 401 handling.
  - Complete page routes: `/login`, `/register`, `/dashboard`, `/contacts`, `/contacts/:id`, `/templates`, `/templates/new`, `/templates/:id/edit`, `/campaigns`, `/campaigns/new`, `/campaigns/:id`, `/campaigns/:id/analytics`, `/analytics`, `/settings`.
  - Sandboxed iframe HTML email preview (`SafeHtmlPreview`) for isolated, safe template design.
  - Real-time polling trackers for bulk CSV imports and asynchronous campaign delivery dispatches.
- **V6 (Production Email Delivery & Campaign Scheduling)**:
  - **Production SMTP Transport**: Implemented `SMTPProvider` using `aiosmtplib` with SSL/STARTTLS support, custom timeouts, formatted MIME multipart messages (HTML + plain text fallback), and fine-grained transient (4xx / network timeouts) vs permanent (5xx) error categorization.
  - **Sender Identity & Overrides**: Extended `EmailCampaign` model and schemas with custom `from_name`, `from_email`, and `reply_to` fields, falling back to global system sender identity when not set.
  - **Timezone-Aware Scheduling**: Added `scheduled_at` (UTC timestamp) and `timezone` to `EmailCampaign`. Added `POST /api/v1/campaigns/{campaign_id}/schedule` endpoint with future UTC date validation and IANA timezone verification (`zoneinfo`).
  - **Campaign Cancellation**: Implemented `POST /api/v1/campaigns/{campaign_id}/cancel` allowing users to halt `SCHEDULED`, `QUEUED`, or `READY` campaigns safely.
  - **Celery Beat Periodic Scheduler**: Configured Celery Beat periodic task `check_scheduled_campaigns_task` (runs every 30s) that queries due scheduled campaigns using PostgreSQL row locking (`SELECT ... FOR UPDATE SKIP LOCKED`), snapshots recipients, transitions state to `QUEUED`, and dispatches worker execution tasks.
  - **Distributed Rate Limiting**: Built Redis token-bucket `DistributedRateLimiter` (`app/core/rate_limiter.py`) pacing email dispatches across concurrent Celery worker processes to conform to `EMAIL_RATE_LIMIT_PER_SECOND`.
  - **Frontend Scheduling Integration**: Added "Schedule for Later" and "Cancel Scheduled Campaign" modals to `CampaignDetailPage`, added `scheduled` and `cancelled` badges and filters to `CampaignsPage`, and updated `CampaignAnalyticsPage` and `CampaignCreatePage`.
  - **Database Migration**: Applied Alembic migration `006_v6_scheduling_and_delivery.py`.
  - **Docker Compose**: Added `beat` container (`sherify_beat`) running `celery beat`.
  - **Testing**: 123 backend tests (100% pass) + 11 frontend Vitest tests (100% pass) + frontend production build validated.

---

## 🏛️ Database Architecture

### Domain Models
1. **`User`** (`users` table): `id` (UUID PK), `email` (Unique, Indexed), `password_hash`, `is_active`, timestamps.
2. **`ContactList`** (`contact_lists` table): `id` (UUID PK), `owner_id` (FK `users.id` ON DELETE CASCADE), `name`, `description`, timestamps.
3. **`Subscriber`** (`subscribers` table): `id` (UUID PK), `contact_list_id` (FK `contact_lists.id` ON DELETE CASCADE), `email`, `first_name`, `last_name`, `status`, `metadata` (JSON), timestamps. Unique on `(contact_list_id, email)`.
4. **`EmailTemplate`** (`email_templates` table): `id` (UUID PK), `owner_id` (FK `users.id` ON DELETE CASCADE), `name`, `subject`, `html_content`, `text_content`, timestamps.
5. **`EmailCampaign`** (`email_campaigns` table):
   - `id`: UUID (PK)
   - `owner_id`: UUID (FK `users.id` ON DELETE CASCADE, Indexed)
   - `name`: VARCHAR(255)
   - `subject`: VARCHAR(255)
   - `template_id`: UUID (FK `email_templates.id` ON DELETE RESTRICT, Indexed)
   - `contact_list_id`: UUID (FK `contact_lists.id` ON DELETE RESTRICT, Indexed)
   - `status`: VARCHAR(50) (Indexed: `draft`, `ready`, `scheduled`, `queued`, `sending`, `completed`, `failed`, `cancelled`)
   - `scheduled_at`: TIMESTAMP WITH TIME ZONE (Nullable, Indexed)
   - `timezone`: VARCHAR(50) (Nullable)
   - `from_name`: VARCHAR(255) (Nullable)
   - `from_email`: VARCHAR(255) (Nullable)
   - `reply_to`: VARCHAR(255) (Nullable)
   - timestamps
6. **`CampaignRecipient`** (`campaign_recipients` table):
   - `id`: UUID (PK)
   - `campaign_id`: UUID (FK `email_campaigns.id` ON DELETE CASCADE, Indexed)
   - `subscriber_id`: UUID (FK `subscribers.id` ON DELETE SET NULL, Indexed)
   - `email`: VARCHAR(255)
   - `tracking_token`: VARCHAR(64) (Unique, Indexed)
   - `status`: VARCHAR(50) (Indexed: `pending`, `processing`, `sent`, `failed`, `bounced`)
   - `attempts`: INTEGER
   - `provider_message_id`: VARCHAR(255) (Indexed)
   - `error_message`: TEXT (Nullable)
   - `sent_at`: TIMESTAMP WITH TIME ZONE (Nullable)
   - `failed_at`: TIMESTAMP WITH TIME ZONE (Nullable)
   - `opened_at`: TIMESTAMP WITH TIME ZONE (Nullable)
   - `bounced_at`: TIMESTAMP WITH TIME ZONE (Nullable)
   - timestamps
7. **`ImportJob`** (`import_jobs` table): `id`, `owner_id`, `contact_list_id`, `status`, `original_filename`, `file_path`, row counters, `completed_at`, timestamps.
8. **`ImportError`** (`import_errors` table): `id`, `import_job_id`, `row_number`, `error_type`, `message`, `created_at`.
9. **`TrackingEvent`** (`tracking_events` table): `id`, `campaign_id`, `campaign_recipient_id`, `event_type`, `occurred_at`, `received_at`, `provider_event_id`, `created_at`.
10. **`WebhookEvent`** (`webhook_events` table): `id`, `provider`, `provider_event_id`, `event_type`, `payload_json`, `status`, `error_message`, `received_at`, `processed_at`, timestamps. Unique on `(provider, provider_event_id)`.

---

## 🗺️ Version Roadmap

- [x] **V1 (Audience Management)**: Complete
- [x] **V2 (Campaign Engine)**: Complete
- [x] **V3 (Celery Campaign Execution)**: Complete
- [x] **V4 (Bulk Data Management)**: Complete
- [x] **V5 (Tracking & Webhooks)**: Complete
- [x] **Frontend V1 (Campaign Manager Dashboard)**: Complete
- [x] **V6 (Production Email Delivery & Campaign Scheduling)**: Complete
- [ ] **V7 (Compliance & Unsubscribe)**: Planned
- [ ] **V8 (Template Variables)**: Planned
- [ ] **V9 (Click Tracking)**: Planned
- [ ] **V10 (Analytics Dashboard)**: Planned
