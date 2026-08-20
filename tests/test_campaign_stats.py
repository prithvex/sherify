from datetime import datetime, timezone
from typing import Dict
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.recipient import CampaignRecipient
from app.models.user import User


@pytest.mark.asyncio
async def test_campaign_stats_calculation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    user_a: User,
    auth_headers_a: Dict[str, str],
    campaign_a: EmailCampaign,
):
    """
    Test exact SQL-aggregated statistics for a campaign with 100 recipients:
    80 sent (40 opened), 10 failed, 10 bounced.
    """
    now_utc = datetime.now(timezone.utc)
    recipients = []

    # 1. 40 Sent and Opened
    for i in range(40):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign_a.id,
                email=f"sent_opened_{i}@example.com",
                tracking_token=f"token_opened_{i}",
                status="sent",
                sent_at=now_utc,
                opened_at=now_utc,
            )
        )

    # 2. 40 Sent and Not Opened
    for i in range(40):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign_a.id,
                email=f"sent_unopened_{i}@example.com",
                tracking_token=f"token_unopened_{i}",
                status="sent",
                sent_at=now_utc,
                opened_at=None,
            )
        )

    # 3. 10 Failed
    for i in range(10):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign_a.id,
                email=f"failed_{i}@example.com",
                tracking_token=f"token_failed_{i}",
                status="failed",
                failed_at=now_utc,
            )
        )

    # 4. 10 Bounced
    for i in range(10):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign_a.id,
                email=f"bounced_{i}@example.com",
                tracking_token=f"token_bounced_{i}",
                status="bounced",
                sent_at=now_utc,
                bounced_at=now_utc,
            )
        )

    db_session.add_all(recipients)
    await db_session.commit()

    response = await async_client.get(
        f"/api/v1/campaigns/{campaign_a.id}/stats",
        headers=auth_headers_a,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["campaign_id"] == str(campaign_a.id)
    assert data["total_recipients"] == 100
    assert data["sent_count"] == 90  # 80 sent + 10 bounced (were previously dispatched)
    assert data["failed_count"] == 10
    assert data["bounced_count"] == 10
    assert data["opened_count"] == 40
    assert data["open_rate"] == round(40 / 90, 4)
    assert data["bounce_rate"] == round(10 / 90, 4)


@pytest.mark.asyncio
async def test_campaign_stats_zero_recipients_division_by_zero_safety(
    async_client: AsyncClient,
    user_a: User,
    auth_headers_a: Dict[str, str],
    campaign_a: EmailCampaign,
):
    """
    Test stats calculation for a brand new campaign with 0 recipients safely yields 0.0 rates.
    """
    response = await async_client.get(
        f"/api/v1/campaigns/{campaign_a.id}/stats",
        headers=auth_headers_a,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_recipients"] == 0
    assert data["sent_count"] == 0
    assert data["failed_count"] == 0
    assert data["bounced_count"] == 0
    assert data["opened_count"] == 0
    assert data["open_rate"] == 0.0
    assert data["bounce_rate"] == 0.0


@pytest.mark.asyncio
async def test_campaign_stats_cross_user_isolation(
    async_client: AsyncClient,
    auth_headers_b: Dict[str, str],
    campaign_a: EmailCampaign,
):
    """
    Test user B cannot access campaign stats for campaign owned by user A (returns 404).
    """
    response = await async_client.get(
        f"/api/v1/campaigns/{campaign_a.id}/stats",
        headers=auth_headers_b,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_campaign_stats_unauthenticated_rejected(
    async_client: AsyncClient,
    campaign_a: EmailCampaign,
):
    """
    Test unauthenticated access to campaign stats is rejected with 401.
    """
    response = await async_client.get(f"/api/v1/campaigns/{campaign_a.id}/stats")
    assert response.status_code == 401
