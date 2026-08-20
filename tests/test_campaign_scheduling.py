from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList
from app.models.template import EmailTemplate
from app.models.user import User
from app.services.campaign_service import campaign_service


@pytest.mark.asyncio
async def test_schedule_ready_campaign_success(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    # 1. Add active subscriber to contact list
    sub_res = await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "active_subscriber@example.com"},
    )
    assert sub_res.status_code == 201

    # 2. Create Draft Campaign
    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Holiday Promo",
            "subject": "Exclusive Discount",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
            "from_name": "Acme Deals",
            "from_email": "deals@acme.com",
            "reply_to": "support@acme.com",
        },
    )
    assert camp_res.status_code == 201
    camp_id = camp_res.json()["id"]

    # 3. Mark Campaign READY
    ready_res = await async_client.post(f"/api/v1/campaigns/{camp_id}/ready", headers=auth_headers_a)
    assert ready_res.status_code == 200
    assert ready_res.json()["status"] == "ready"

    # 4. Schedule Campaign for 2 hours in the future
    future_utc = datetime.now(timezone.utc) + timedelta(hours=2)
    schedule_res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_a,
        json={
            "scheduled_at": future_utc.isoformat(),
            "timezone": "Asia/Kolkata",
        },
    )
    assert schedule_res.status_code == 200
    data = schedule_res.json()
    assert data["status"] == "scheduled"
    assert data["timezone"] == "Asia/Kolkata"
    assert data["from_name"] == "Acme Deals"
    assert data["from_email"] == "deals@acme.com"
    assert data["scheduled_at"] is not None


@pytest.mark.asyncio
async def test_schedule_campaign_past_datetime_rejected(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "sub1@example.com"},
    )

    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Past Campaign",
            "subject": "Past Subject",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    camp_id = camp_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{camp_id}/ready", headers=auth_headers_a)

    past_utc = datetime.now(timezone.utc) - timedelta(minutes=10)
    res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_a,
        json={
            "scheduled_at": past_utc.isoformat(),
            "timezone": "UTC",
        },
    )
    assert res.status_code == 400
    assert "future" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_schedule_campaign_invalid_timezone_rejected(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "sub2@example.com"},
    )

    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Invalid TZ Campaign",
            "subject": "Invalid TZ",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    camp_id = camp_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{camp_id}/ready", headers=auth_headers_a)

    future_utc = datetime.now(timezone.utc) + timedelta(hours=1)
    res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_a,
        json={
            "scheduled_at": future_utc.isoformat(),
            "timezone": "NonExistent/Timezone_Invalid",
        },
    )
    assert res.status_code == 400
    assert "invalid timezone" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_schedule_draft_campaign_rejected(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Draft Schedule",
            "subject": "Draft Subject",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    camp_id = camp_res.json()["id"]

    future_utc = datetime.now(timezone.utc) + timedelta(hours=1)
    res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_a,
        json={
            "scheduled_at": future_utc.isoformat(),
            "timezone": "UTC",
        },
    )
    assert res.status_code == 400
    assert "ready" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancel_scheduled_campaign_success(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "sub_cancel@example.com"},
    )

    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Cancel Promo",
            "subject": "Cancel Subject",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    camp_id = camp_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{camp_id}/ready", headers=auth_headers_a)

    future_utc = datetime.now(timezone.utc) + timedelta(hours=5)
    await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_a,
        json={
            "scheduled_at": future_utc.isoformat(),
            "timezone": "America/New_York",
        },
    )

    # Cancel Campaign
    cancel_res = await async_client.post(f"/api/v1/campaigns/{camp_id}/cancel", headers=auth_headers_a)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify Detail reflects cancelled
    get_res = await async_client.get(f"/api/v1/campaigns/{camp_id}", headers=auth_headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cross_user_scheduling_isolation(
    async_client: AsyncClient,
    auth_headers_a: dict,
    auth_headers_b: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "sub_user1@example.com"},
    )

    camp_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "User 1 Campaign",
            "subject": "Subject 1",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    camp_id = camp_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{camp_id}/ready", headers=auth_headers_a)

    future_utc = datetime.now(timezone.utc) + timedelta(hours=1)

    # User B attempts to schedule User A's campaign
    res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/schedule",
        headers=auth_headers_b,
        json={
            "scheduled_at": future_utc.isoformat(),
            "timezone": "UTC",
        },
    )
    assert res.status_code == 404

    # User B attempts to cancel User A's campaign
    cancel_res = await async_client.post(
        f"/api/v1/campaigns/{camp_id}/cancel",
        headers=auth_headers_b,
    )
    assert cancel_res.status_code == 404


@pytest.mark.asyncio
async def test_celery_beat_scheduler_triggers_due_campaigns(
    async_client: AsyncClient,
    auth_headers_a: dict,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
    user_a: User,
    db_session: AsyncSession,
):
    # Add active subscriber
    await async_client.post(
        f"/api/v1/contact-lists/{contact_list_a.id}/subscribers",
        headers=auth_headers_a,
        json={"email": "beat_recipient@example.com"},
    )

    # Create Campaign 1: Due in the past (scheduled_at = now - 5 minutes)
    c1_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Due Campaign",
            "subject": "Due Subject",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    c1_id = c1_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{c1_id}/ready", headers=auth_headers_a)

    # Force c1 into scheduled state with past scheduled_at directly
    past_dt = datetime.now(timezone.utc) - timedelta(minutes=5)
    c1_db = await campaign_service.get_by_id(db_session, campaign_id=c1_id, owner_id=user_a.id)
    c1_db.status = "scheduled"
    c1_db.scheduled_at = past_dt
    c1_db.timezone = "UTC"
    await db_session.commit()

    # Create Campaign 2: Future scheduled (scheduled_at = now + 2 hours)
    c2_res = await async_client.post(
        "/api/v1/campaigns",
        headers=auth_headers_a,
        json={
            "name": "Future Campaign",
            "subject": "Future Subject",
            "template_id": str(template_a.id),
            "contact_list_id": str(contact_list_a.id),
        },
    )
    c2_id = c2_res.json()["id"]
    await async_client.post(f"/api/v1/campaigns/{c2_id}/ready", headers=auth_headers_a)
    future_dt = datetime.now(timezone.utc) + timedelta(hours=2)
    await async_client.post(
        f"/api/v1/campaigns/{c2_id}/schedule",
        headers=auth_headers_a,
        json={"scheduled_at": future_dt.isoformat(), "timezone": "UTC"},
    )

    # Run Celery Beat trigger logic
    with patch("app.tasks.campaign_tasks.execute_campaign_task.delay") as mock_delay:
        triggered = await campaign_service.trigger_due_scheduled_campaigns(db_session)
        assert triggered == 1

        # Check mock called with c1_id
        mock_delay.assert_called_once_with(str(c1_id))

        # Check c1 is now QUEUED
        c1_refreshed = await campaign_service.get_by_id(db_session, campaign_id=c1_id, owner_id=user_a.id)
        assert c1_refreshed.status == "queued"

        # Check c2 remains SCHEDULED
        c2_refreshed = await campaign_service.get_by_id(db_session, campaign_id=c2_id, owner_id=user_a.id)
        assert c2_refreshed.status == "scheduled"
