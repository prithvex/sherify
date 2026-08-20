from datetime import datetime, timezone
from typing import List
from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.contact_list import ContactList
from app.models.recipient import CampaignRecipient
from app.models.subscriber import Subscriber
from app.models.template import EmailTemplate
from app.models.user import User
from app.services.campaign_execution_service import campaign_execution_service


@pytest.mark.asyncio
async def test_execution_scenario_a_all_succeed(
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    """
    Scenario A: 100 recipients, all succeed.
    Expected:
    - 100 SENT
    - Campaign: COMPLETED
    """
    # 1. Create campaign in QUEUED status
    campaign = EmailCampaign(
        owner_id=user_a.id,
        name="Scenario A Campaign",
        subject="100 Success Subject",
        template_id=template_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    # 2. Create 100 recipient records in PENDING status
    recipients = [
        CampaignRecipient(
            campaign_id=campaign.id,
            email=f"valid_user_{i:03d}@example.com",
            status="pending",
            attempts=0,
        )
        for i in range(100)
    ]
    db_session.add_all(recipients)
    await db_session.commit()

    # 3. Execute campaign
    await campaign_execution_service.execute_campaign(campaign_id=campaign.id, db=db_session)

    # 4. Verify DB state
    await db_session.refresh(campaign)
    assert campaign.status == "completed"

    res = await db_session.execute(
        select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign.id)
    )
    all_recipients = list(res.scalars().all())
    assert len(all_recipients) == 100
    for r in all_recipients:
        assert r.status == "sent"
        assert r.attempts == 1
        assert r.provider_message_id is not None
        assert r.sent_at is not None
        assert r.error_message is None


@pytest.mark.asyncio
async def test_execution_scenario_b_partial_permanent_failures(
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    """
    Scenario B: 100 recipients, 5 fail permanently (fail@...).
    Expected:
    - 95 SENT
    - 5 FAILED
    - Campaign: COMPLETED (execution finished all intended recipients)
    """
    campaign = EmailCampaign(
        owner_id=user_a.id,
        name="Scenario B Campaign",
        subject="Partial Failure Subject",
        template_id=template_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    recipients = []
    # 95 valid
    for i in range(95):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign.id,
                email=f"valid_{i:03d}@example.com",
                status="pending",
                attempts=0,
            )
        )
    # 5 permanent failures
    for i in range(5):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign.id,
                email=f"fail_{i:03d}@example.com",
                status="pending",
                attempts=0,
            )
        )
    db_session.add_all(recipients)
    await db_session.commit()

    # Execute
    await campaign_execution_service.execute_campaign(campaign_id=campaign.id, db=db_session)

    # Verify Campaign status
    await db_session.refresh(campaign)
    assert campaign.status == "completed"

    res = await db_session.execute(
        select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign.id)
    )
    all_recipients = list(res.scalars().all())
    sent_count = sum(1 for r in all_recipients if r.status == "sent")
    failed_count = sum(1 for r in all_recipients if r.status == "failed")
    assert sent_count == 95
    assert failed_count == 5


@pytest.mark.asyncio
async def test_execution_scenario_c_crash_recovery_and_idempotency(
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    """
    Scenario C: 100 recipients.
    Worker already sent 50 recipients before crashing.
    Task retries.
    Expected:
    - The 50 already SENT recipients are NOT sent again (attempts remain 1).
    - The remaining 50 PENDING recipients are sent.
    - Final state: 100 SENT, campaign COMPLETED.
    """
    campaign = EmailCampaign(
        owner_id=user_a.id,
        name="Scenario C Campaign",
        subject="Crash Recovery Subject",
        template_id=template_a.id,
        contact_list_id=contact_list_a.id,
        status="sending",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    recipients = []
    # 50 already sent before crash
    for i in range(50):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign.id,
                email=f"already_sent_{i:03d}@example.com",
                status="sent",
                attempts=1,
                provider_message_id=f"prior-msg-{i}",
                sent_at=datetime.now(timezone.utc),
            )
        )
    # 50 still pending
    for i in range(50):
        recipients.append(
            CampaignRecipient(
                campaign_id=campaign.id,
                email=f"remaining_pending_{i:03d}@example.com",
                status="pending",
                attempts=0,
            )
        )
    db_session.add_all(recipients)
    await db_session.commit()

    # Retry execution
    await campaign_execution_service.execute_campaign(campaign_id=campaign.id, db=db_session)

    # Verify Campaign status
    await db_session.refresh(campaign)
    assert campaign.status == "completed"

    res = await db_session.execute(
        select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign.id)
    )
    all_recipients = list(res.scalars().all())
    assert len(all_recipients) == 100
    for r in all_recipients:
        assert r.status == "sent"
        assert r.attempts == 1  # Verify prior 50 were NOT incremented again


@pytest.mark.asyncio
async def test_recipient_snapshot_email_preservation(
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
):
    """
    Test that CampaignRecipient retains original email address snapshot
    even if the subscriber's email changes later.
    """
    # 1. Create Subscriber with initial email
    subscriber = Subscriber(
        contact_list_id=contact_list_a.id,
        email="original_email@example.com",
        status="active",
    )
    db_session.add(subscriber)
    await db_session.commit()
    await db_session.refresh(subscriber)

    # 2. Create Campaign & Recipient snapshot
    campaign = EmailCampaign(
        owner_id=user_a.id,
        name="Snapshot Test",
        subject="Snapshot Sub",
        template_id=template_a.id,
        contact_list_id=contact_list_a.id,
        status="queued",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)

    recipient = CampaignRecipient(
        campaign_id=campaign.id,
        subscriber_id=subscriber.id,
        email=subscriber.email,
        status="pending",
        attempts=0,
    )
    db_session.add(recipient)
    await db_session.commit()

    # 3. Subscriber changes their email later
    subscriber.email = "new_changed_email@example.com"
    await db_session.commit()

    # 4. Execute campaign
    await campaign_execution_service.execute_campaign(campaign_id=campaign.id, db=db_session)

    # 5. Verify recipient still retains the snapshot email
    await db_session.refresh(recipient)
    assert recipient.email == "original_email@example.com"
    assert recipient.status == "sent"
