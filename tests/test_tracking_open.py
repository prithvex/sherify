import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.contact_list import ContactList
from app.models.recipient import CampaignRecipient
from app.models.template import EmailTemplate
from app.models.tracking import TrackingEvent
from app.models.user import User
from app.services.campaign_execution_service import campaign_execution_service
from app.services.tracking_service import TRANSPARENT_GIF_BYTES


@pytest.mark.asyncio
async def test_track_email_open_valid_token(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
    campaign_a: EmailCampaign,
):
    """
    Test valid tracking token records first-open timestamp, creates TrackingEvent, and returns 1x1 GIF.
    """
    token = "test_secure_tracking_token_12345"
    recipient = CampaignRecipient(
        campaign_id=campaign_a.id,
        email="test_recipient@example.com",
        tracking_token=token,
        status="sent",
    )
    db_session.add(recipient)
    await db_session.commit()
    await db_session.refresh(recipient)

    response = await async_client.get(f"/track/open/{token}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert response.headers["cache-control"] == "no-cache, no-store, must-revalidate, max-age=0"
    assert response.content == TRANSPARENT_GIF_BYTES

    # Verify recipient opened_at is set
    await db_session.refresh(recipient)
    assert recipient.opened_at is not None

    # Verify TrackingEvent record created
    stmt = select(TrackingEvent).where(TrackingEvent.campaign_recipient_id == recipient.id)
    result = await db_session.execute(stmt)
    events = list(result.scalars().all())
    assert len(events) == 1
    assert events[0].event_type == "opened"
    assert events[0].campaign_id == campaign_a.id


@pytest.mark.asyncio
async def test_track_email_open_repeated_requests_idempotent(
    async_client: AsyncClient,
    db_session: AsyncSession,
    campaign_a: EmailCampaign,
):
    """
    Test requesting the tracking pixel multiple times retains the first open timestamp and does not create duplicate events.
    """
    token = "test_idempotent_token_67890"
    recipient = CampaignRecipient(
        campaign_id=campaign_a.id,
        email="repeat_recipient@example.com",
        tracking_token=token,
        status="sent",
    )
    db_session.add(recipient)
    await db_session.commit()
    await db_session.refresh(recipient)

    # 1st Open
    res1 = await async_client.get(f"/track/open/{token}")
    assert res1.status_code == 200
    await db_session.refresh(recipient)
    first_opened_at = recipient.opened_at
    assert first_opened_at is not None

    # Repeated Opens (2nd to 5th)
    for _ in range(4):
        res = await async_client.get(f"/track/open/{token}")
        assert res.status_code == 200
        assert res.content == TRANSPARENT_GIF_BYTES

    # Check recipient opened_at unchanged
    await db_session.refresh(recipient)
    assert recipient.opened_at == first_opened_at

    # Check only 1 TrackingEvent in database
    stmt = select(TrackingEvent).where(TrackingEvent.campaign_recipient_id == recipient.id)
    result = await db_session.execute(stmt)
    events = list(result.scalars().all())
    assert len(events) == 1


@pytest.mark.asyncio
async def test_track_email_open_invalid_token_returns_gif(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test invalid or nonexistent tracking token returns 1x1 GIF silently without leaking data.
    """
    response = await async_client.get("/track/open/completely_invalid_nonexistent_token")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert response.content == TRANSPARENT_GIF_BYTES

    # No tracking events in database
    stmt = select(TrackingEvent)
    result = await db_session.execute(stmt)
    assert len(list(result.scalars().all())) == 0


@pytest.mark.asyncio
async def test_tracking_pixel_html_injection():
    """
    Unit test for tracking pixel injection into HTML template content.
    """
    html_with_body = "<html><body><h1>Hello World</h1></body></html>"
    token = "test_pixel_token_123"

    injected = campaign_execution_service._inject_tracking_pixel(html_with_body, token)
    assert f"/track/open/{token}" in injected
    assert '<img src="http://localhost:8000/track/open/test_pixel_token_123" width="1" height="1" style="display:none" alt="" /></body>' in injected

    # HTML without body tag
    html_raw = "<div>Simple snippet</div>"
    injected_raw = campaign_execution_service._inject_tracking_pixel(html_raw, token)
    assert injected_raw.endswith(f'<img src="http://localhost:8000/track/open/{token}" width="1" height="1" style="display:none" alt="" />')

    # None handling
    assert campaign_execution_service._inject_tracking_pixel(None, token) is None
