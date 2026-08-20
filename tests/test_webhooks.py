from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.recipient import CampaignRecipient
from app.models.tracking import TrackingEvent, WebhookEvent
from app.services.webhook_execution_service import webhook_execution_service


@pytest.mark.asyncio
async def test_webhook_valid_signature_ingestion(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test valid webhook request signature is accepted and persisted with status 'received' (HTTP 202).
    """
    payload = {
        "event_id": "mock_evt_1001",
        "event_type": "bounce",
        "message_id": "mock_msg_5001",
        "email": "bounced.user@example.com",
        "timestamp": 1700000000,
    }
    headers = {"X-Webhook-Signature": "mock-valid-signature"}

    response = await async_client.post(
        "/api/v1/webhooks/email/mock",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "received"
    assert "event_id" in data

    # Verify WebhookEvent stored in database
    stmt = select(WebhookEvent).where(WebhookEvent.provider_event_id == "mock_evt_1001")
    result = await db_session.execute(stmt)
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.provider == "mock"
    assert event.event_type == "bounced"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test webhook with missing or invalid signature is rejected with HTTP 401.
    """
    payload = {"event_id": "mock_evt_invalid", "event_type": "bounce"}

    # Missing header
    res1 = await async_client.post("/api/v1/webhooks/email/mock", json=payload)
    assert res1.status_code == 401

    # Invalid header
    res2 = await async_client.post(
        "/api/v1/webhooks/email/mock",
        json=payload,
        headers={"X-Webhook-Signature": "completely-invalid-signature"},
    )
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_webhook_duplicate_event_deduplication(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test receiving the same provider event ID multiple times is deduplicated idempotently.
    """
    payload = {
        "event_id": "mock_duplicate_evt",
        "event_type": "bounce",
        "message_id": "mock_msg_dup",
    }
    headers = {"X-Webhook-Signature": "mock-valid-signature"}

    # First dispatch
    res1 = await async_client.post("/api/v1/webhooks/email/mock", json=payload, headers=headers)
    assert res1.status_code == 202
    data1 = res1.json()

    # Second dispatch
    res2 = await async_client.post("/api/v1/webhooks/email/mock", json=payload, headers=headers)
    assert res2.status_code == 202
    data2 = res2.json()

    assert data1["event_id"] == data2["event_id"]

    # Verify only 1 WebhookEvent record exists in DB
    stmt = select(WebhookEvent).where(WebhookEvent.provider_event_id == "mock_duplicate_evt")
    result = await db_session.execute(stmt)
    events = list(result.scalars().all())
    assert len(events) == 1


@pytest.mark.asyncio
async def test_webhook_execution_bounce_processing(
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
):
    """
    Test worker execution for a BOUNCE webhook updates recipient status, sets bounced_at, and records TrackingEvent.
    """
    sent_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    bounce_time = datetime(2026, 8, 20, 10, 5, 0, tzinfo=timezone.utc)

    # 1. Create a SENT recipient
    recipient = CampaignRecipient(
        campaign_id=campaign_a.id,
        email="bounce_test@example.com",
        tracking_token="token_bounce_test",
        status="sent",
        provider_message_id="prov_msg_bounce_100",
        sent_at=sent_time,
    )
    db_session.add(recipient)

    # 2. Create WebhookEvent
    webhook_event = WebhookEvent(
        provider="mock",
        provider_event_id="prov_evt_bounce_100",
        event_type="bounced",
        payload_json={
            "event_id": "prov_evt_bounce_100",
            "event_type": "bounce",
            "message_id": "prov_msg_bounce_100",
            "email": "bounce_test@example.com",
            "timestamp": int(bounce_time.timestamp()),
        },
        status="received",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(webhook_event)
    await db_session.commit()
    await db_session.refresh(recipient)
    await db_session.refresh(webhook_event)

    # 3. Execute webhook processing
    await webhook_execution_service.execute_webhook(
        webhook_event_id=webhook_event.id,
        task_id="test-task-bounce",
        db=db_session,
    )

    # 4. Verify recipient state
    await db_session.refresh(recipient)
    assert recipient.status == "bounced"
    assert recipient.bounced_at is not None
    assert recipient.sent_at == sent_time  # Preserved sent_at

    # 5. Verify TrackingEvent
    stmt = select(TrackingEvent).where(TrackingEvent.campaign_recipient_id == recipient.id)
    result = await db_session.execute(stmt)
    tracking_events = list(result.scalars().all())
    assert len(tracking_events) == 1
    assert tracking_events[0].event_type == "bounced"
    assert tracking_events[0].provider_event_id == "prov_evt_bounce_100"

    # 6. Verify WebhookEvent status
    await db_session.refresh(webhook_event)
    assert webhook_event.status == "processed"
    assert webhook_event.processed_at is not None


@pytest.mark.asyncio
async def test_webhook_execution_unresolved_message_id_handled(
    db_session: AsyncSession,
):
    """
    Test that webhook referencing an unknown provider_message_id marks status 'ignored' without crashing.
    """
    webhook_event = WebhookEvent(
        provider="mock",
        provider_event_id="unresolved_evt_1",
        event_type="bounced",
        payload_json={
            "event_id": "unresolved_evt_1",
            "event_type": "bounce",
            "message_id": "nonexistent_provider_msg_id",
        },
        status="received",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(webhook_event)
    await db_session.commit()
    await db_session.refresh(webhook_event)

    await webhook_execution_service.execute_webhook(
        webhook_event_id=webhook_event.id,
        task_id="test-unresolved",
        db=db_session,
    )

    await db_session.refresh(webhook_event)
    assert webhook_event.status == "ignored"
    assert "No recipient found" in (webhook_event.error_message or "")


@pytest.mark.asyncio
async def test_webhook_execution_unsupported_event_type_handled(
    db_session: AsyncSession,
):
    """
    Test that unsupported provider event types mark status 'ignored' gracefully.
    """
    webhook_event = WebhookEvent(
        provider="mock",
        provider_event_id="unsupported_evt_1",
        event_type="unsupported",
        payload_json={
            "event_id": "unsupported_evt_1",
            "event_type": "some_random_future_provider_ping",
        },
        status="received",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(webhook_event)
    await db_session.commit()
    await db_session.refresh(webhook_event)

    await webhook_execution_service.execute_webhook(
        webhook_event_id=webhook_event.id,
        task_id="test-unsupported",
        db=db_session,
    )

    await db_session.refresh(webhook_event)
    assert webhook_event.status == "ignored"
    assert "Unsupported event type" in (webhook_event.error_message or "")


@pytest.mark.asyncio
async def test_webhook_execution_idempotency_and_order_independence(
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
):
    """
    Test that re-running webhook execution does not duplicate TrackingEvents, and open + bounce can coexist.
    """
    open_ts = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)
    bounce_ts = datetime(2026, 8, 20, 12, 5, 0, tzinfo=timezone.utc)

    # Recipient was sent and already opened
    recipient = CampaignRecipient(
        campaign_id=campaign_a.id,
        email="coexist@example.com",
        tracking_token="token_coexist",
        status="sent",
        provider_message_id="msg_coexist_1",
        sent_at=datetime(2026, 8, 20, 11, 55, 0, tzinfo=timezone.utc),
        opened_at=open_ts,
    )
    db_session.add(recipient)
    await db_session.flush()

    open_tracking_event = TrackingEvent(
        campaign_id=campaign_a.id,
        campaign_recipient_id=recipient.id,
        event_type="opened",
        occurred_at=open_ts,
        received_at=open_ts,
    )
    db_session.add(open_tracking_event)

    webhook_event = WebhookEvent(
        provider="mock",
        provider_event_id="evt_coexist_bounce",
        event_type="bounced",
        payload_json={
            "event_id": "evt_coexist_bounce",
            "event_type": "bounce",
            "message_id": "msg_coexist_1",
            "timestamp": int(bounce_ts.timestamp()),
        },
        status="received",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(webhook_event)
    await db_session.commit()

    # Execute bounce webhook
    await webhook_execution_service.execute_webhook(
        webhook_event_id=webhook_event.id,
        task_id="test-coexist",
        db=db_session,
    )

    # Re-run execution (simulating Celery task duplicate execution)
    await webhook_execution_service.execute_webhook(
        webhook_event_id=webhook_event.id,
        task_id="test-coexist-retry",
        db=db_session,
    )

    await db_session.refresh(recipient)
    assert recipient.status == "bounced"
    assert recipient.opened_at == open_ts  # Open retained
    assert recipient.bounced_at is not None  # Bounce set

    # Verify exactly 2 tracking events (1 open, 1 bounce)
    stmt = select(TrackingEvent).where(TrackingEvent.campaign_recipient_id == recipient.id)
    result = await db_session.execute(stmt)
    tracking_events = list(result.scalars().all())
    assert len(tracking_events) == 2
    types = {e.event_type for e in tracking_events}
    assert types == {"opened", "bounced"}
