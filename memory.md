# Persistent Engineering Memory

## Project Status

- **Current Version**: V5 — Tracking & Webhooks
- **Completed Versions**: Initialization, V1 (Audience Management), V2 (Campaign Engine), V3 (Campaign Execution), V4 (Bulk Data Management), V5 (Tracking & Webhooks)
- **Current Development Phase**: V5 Complete
- **Overall Health**: Healthy
- **V5 Status**: Completed

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
  - **Migration & Test Suite**: Alembic migration `005_v5_tracking_and_webhooks`, 108 automated unit/integration tests passing (100%), and live Docker E2E verification.

---

## Tracking

- **Tracking Token**: Cryptographically secure 32-byte URL-safe string generated per `CampaignRecipient` (`secrets.token_urlsafe(32)`).
- **Tracking Pixel**: 1x1 transparent GIF (43 bytes) returned via `GET /track/open/{tracking_token}` with `Cache-Control: no-cache, no-store, must-revalidate, max-age=0`. Injected into outgoing HTML emails before `</body>`.
- **First-Open Behavior & `opened_at`**: Only the first open event populates `opened_at` and generates a `TrackingEvent(event_type="opened")`. Subsequent requests return the GIF without altering the first-open timestamp or duplicating events.

---

## Webhooks

- **Webhook Endpoint**: `POST /api/v1/webhooks/email/{provider}` (public, provider-authenticated).
- **Verification**: `BaseWebhookVerifier` abstraction validating HMAC signatures and timestamps using configured secrets before accepting the payload.
- **Normalized Events**: `BaseWebhookParser` transforms vendor-specific payloads into `NormalizedWebhookEvent` (`provider`, `provider_event_id`, `event_type`, `provider_message_id`, `occurred_at`, `recipient_email`).
- **Idempotency**: Database unique constraint on `(provider, provider_event_id)` in `webhook_events` table ensures duplicate webhook posts return immediate 202 without reprocessing.
- **Celery Processing**: Background worker task `process_webhook_event` processes raw payloads asynchronously, handling unknown event types and unresolved message IDs cleanly as `ignored`.
- **Bounce Handling**: Updates `CampaignRecipient.status = "bounced"` (if previous status was `sent`), sets `CampaignRecipient.bounced_at`, preserves `sent_at`, and records `TrackingEvent(event_type="bounced")`.

---

## Database

### Domain Models
1. **`User`** (`users` table): `id` (UUID PK), `email` (Unique, Indexed), `password_hash`, `is_active`, timestamps.
2. **`ContactList`** (`contact_lists` table): `id` (UUID PK), `owner_id` (FK `users.id` ON DELETE CASCADE), `name`, `description`, timestamps.
3. **`Subscriber`** (`subscribers` table): `id` (UUID PK), `contact_list_id` (FK `contact_lists.id` ON DELETE CASCADE), `email`, `first_name`, `last_name`, `status`, `metadata` (JSON), timestamps. Unique on `(contact_list_id, email)`.
4. **`EmailTemplate`** (`email_templates` table): `id` (UUID PK), `owner_id` (FK `users.id` ON DELETE CASCADE), `name`, `subject`, `html_content`, `text_content`, timestamps.
5. **`EmailCampaign`** (`email_campaigns` table): `id` (UUID PK), `owner_id` (FK `users.id` ON DELETE CASCADE), `name`, `subject`, `template_id` (FK `email_templates.id` ON DELETE RESTRICT), `contact_list_id` (FK `contact_lists.id` ON DELETE RESTRICT), `status` (Default 'draft', Indexed), timestamps.
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
9. **`TrackingEvent`** (`tracking_events` table):
   - `id`: UUID (PK)
   - `campaign_id`: UUID (FK `email_campaigns.id` ON DELETE CASCADE, Indexed)
   - `campaign_recipient_id`: UUID (FK `campaign_recipients.id` ON DELETE CASCADE, Indexed)
   - `event_type`: VARCHAR(50) (Indexed: `opened`, `bounced`)
   - `occurred_at`: TIMESTAMP WITH TIME ZONE
   - `received_at`: TIMESTAMP WITH TIME ZONE
   - `provider_event_id`: VARCHAR(255) (Nullable)
   - `created_at`: TIMESTAMP WITH TIME ZONE
10. **`WebhookEvent`** (`webhook_events` table):
    - `id`: UUID (PK)
    - `provider`: VARCHAR(50)
    - `provider_event_id`: VARCHAR(255)
    - `event_type`: VARCHAR(50)
    - `payload_json`: JSON
    - `status`: VARCHAR(50) (Indexed: `received`, `processing`, `processed`, `ignored`, `failed`)
    - `error_message`: VARCHAR(500) (Nullable)
    - `received_at`: TIMESTAMP WITH TIME ZONE
    - `processed_at`: TIMESTAMP WITH TIME ZONE (Nullable)
    - timestamps
    - Unique Constraint on `(provider, provider_event_id)`

---

## Statistics

- **API Endpoint**: `GET /api/v1/campaigns/{campaign_id}/stats` (Authenticated, Owner only).
- **SQL Aggregation Metrics**:
  - `total_recipients`: `COUNT(id)`
  - `sent_count`: `COUNT(CASE WHEN status IN ('sent', 'bounced') OR sent_at IS NOT NULL THEN 1 END)`
  - `failed_count`: `COUNT(CASE WHEN status = 'failed' THEN 1 END)`
  - `bounced_count`: `COUNT(CASE WHEN status = 'bounced' OR bounced_at IS NOT NULL THEN 1 END)`
  - `opened_count`: `COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)`
  - `open_rate`: `opened_count / sent_count` (0.0 if `sent_count == 0`)
  - `bounce_rate`: `bounced_count / sent_count` (0.0 if `sent_count == 0`)

---

## Architectural Decisions

1. **Tracking events are immutable history**: `TrackingEvent` records historical occurrences and has no update/delete endpoints.
2. **CampaignRecipient remains delivery source of truth**: Tracks current delivery lifecycle and core timestamps (`sent_at`, `failed_at`, `opened_at`, `bounced_at`).
3. **Open and delivery state are separate**: An `opened` event updates `opened_at` without redefining or overwriting `SENT` delivery status.
4. **Webhooks are asynchronous**: Webhook router validates signatures, creates `WebhookEvent`, enqueues Celery, and responds with `HTTP 202 Accepted` immediately.
5. **Webhook events are idempotent**: Enforced at the database layer via unique constraint on `(provider, provider_event_id)`.
6. **Provider-specific webhook payloads are normalized**: `BaseWebhookParser` produces standardized `NormalizedWebhookEvent` instances, decoupling domain logic from provider schemas.
7. **PostgreSQL remains source of truth**: All states, events, and metrics are persisted durably in PostgreSQL.
8. **Tracking URLs use public configuration, not Host headers**: Generated using `settings.PUBLIC_API_BASE_URL`.
9. **No click tracking in V5**: Reserved for future versions.
10. **No unsubscribe/suppression system in V5**: Reserved for future versions.

---

## Current Work

- None.

---

## Roadmap

- **V1 (Audience Management)**: Complete
- **V2 (Campaign Engine)**: Complete
- **V3 (Celery Campaign Execution)**: Complete
- **V4 (Bulk Data Management)**: Complete
- **V5 (Tracking & Webhooks)**: Complete
- **V6 (Scheduling)**: Planned
- **V7 (Compliance & Unsubscribe)**: Planned
- **V8 (Template Variables)**: Planned
- **V9 (Click Tracking)**: Planned
- **V10 (Analytics Dashboard)**: Planned
