import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.recipient import CampaignRecipient
from app.repositories.campaign_repo import campaign_repository
from app.repositories.contact_list_repo import contact_list_repository
from app.repositories.recipient_repo import recipient_repository
from app.repositories.subscriber_repo import subscriber_repository
from app.repositories.template_repo import template_repository
from app.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
    CampaignScheduleRequest,
    CampaignStatus,
    CampaignUpdate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.recipient import RecipientStatus
from app.schemas.tracking import CampaignStatsResponse

logger = logging.getLogger(__name__)


class CampaignService:
    async def _validate_foreign_ownership(
        self,
        db: AsyncSession,
        owner_id: UUID,
        template_id: Optional[UUID] = None,
        contact_list_id: Optional[UUID] = None,
    ) -> None:
        """
        Verify that template and contact list exist and belong to the authenticated user.
        """
        if template_id is not None:
            template = await template_repository.get_by_id(db, template_id=template_id, owner_id=owner_id)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email template not found",
                )

        if contact_list_id is not None:
            contact_list = await contact_list_repository.get_by_id(db, list_id=contact_list_id, owner_id=owner_id)
            if not contact_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Contact list not found",
                )

    async def create(
        self,
        db: AsyncSession,
        owner_id: UUID,
        campaign_in: CampaignCreate,
    ) -> EmailCampaign:
        await self._validate_foreign_ownership(
            db,
            owner_id=owner_id,
            template_id=campaign_in.template_id,
            contact_list_id=campaign_in.contact_list_id,
        )

        campaign = EmailCampaign(
            owner_id=owner_id,
            name=campaign_in.name.strip(),
            subject=campaign_in.subject.strip(),
            template_id=campaign_in.template_id,
            contact_list_id=campaign_in.contact_list_id,
            status=CampaignStatus.DRAFT.value,
            from_name=campaign_in.from_name.strip() if campaign_in.from_name else None,
            from_email=str(campaign_in.from_email).strip().lower() if campaign_in.from_email else None,
            reply_to=str(campaign_in.reply_to).strip().lower() if campaign_in.reply_to else None,
        )
        return await campaign_repository.create(db, campaign)

    async def get_by_id(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        campaign = await campaign_repository.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email campaign not found",
            )
        return campaign

    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[CampaignResponse]:
        items, total = await campaign_repository.list_by_owner(
            db,
            owner_id=owner_id,
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        response_items = [CampaignResponse.model_validate(item) for item in items]
        return PaginatedResponse[CampaignResponse](
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
        campaign_in: CampaignUpdate,
    ) -> EmailCampaign:
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        # READY and other advanced statuses are immutable
        if campaign.status != CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot edit campaign in '{campaign.status.upper()}' status. Only DRAFT campaigns can be modified.",
            )

        if campaign_in.template_id is not None or campaign_in.contact_list_id is not None:
            await self._validate_foreign_ownership(
                db,
                owner_id=owner_id,
                template_id=campaign_in.template_id,
                contact_list_id=campaign_in.contact_list_id,
            )

        if campaign_in.name is not None:
            campaign.name = campaign_in.name.strip()
        if campaign_in.subject is not None:
            campaign.subject = campaign_in.subject.strip()
        if campaign_in.template_id is not None:
            campaign.template_id = campaign_in.template_id
        if campaign_in.contact_list_id is not None:
            campaign.contact_list_id = campaign_in.contact_list_id
        if campaign_in.from_name is not None:
            campaign.from_name = campaign_in.from_name.strip() if campaign_in.from_name else None
        if campaign_in.from_email is not None:
            campaign.from_email = str(campaign_in.from_email).strip().lower() if campaign_in.from_email else None
        if campaign_in.reply_to is not None:
            campaign.reply_to = str(campaign_in.reply_to).strip().lower() if campaign_in.reply_to else None

        return await campaign_repository.update(db, campaign)

    async def delete(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> None:
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)
        await campaign_repository.delete(db, campaign)

    async def transition_ready(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        """
        Validate and atomically transition a campaign from DRAFT to READY.
        """
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        if campaign.status == CampaignStatus.READY.value:
            return campaign

        # 1. Validate campaign name
        if not campaign.name or not campaign.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must have a valid non-empty name before transitioning to READY",
            )

        # 2. Validate campaign subject
        if not campaign.subject or not campaign.subject.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must have a valid non-empty subject before transitioning to READY",
            )

        # 3. Validate template exists and belongs to user
        template = await template_repository.get_by_id(db, template_id=campaign.template_id, owner_id=owner_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced template does not exist or does not belong to the user",
            )

        # 4. Validate contact list exists and belongs to user
        contact_list = await contact_list_repository.get_by_id(db, list_id=campaign.contact_list_id, owner_id=owner_id)
        if not contact_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced contact list does not exist or does not belong to the user",
            )

        # Transition state
        campaign.status = CampaignStatus.READY.value
        return await campaign_repository.update(db, campaign)

    async def _snapshot_recipients(
        self,
        db: AsyncSession,
        campaign: EmailCampaign,
    ) -> int:
        """
        Snapshot all active subscribers into CampaignRecipient records with unique tracking tokens.
        """
        active_count = await subscriber_repository.count_active_subscribers(
            db,
            contact_list_id=campaign.contact_list_id,
        )
        if active_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send/schedule campaign: Referenced contact list has no active subscribers.",
            )

        offset = 0
        batch_limit = 500
        while offset < active_count:
            subscribers_batch = await subscriber_repository.get_active_subscribers_batch(
                db,
                contact_list_id=campaign.contact_list_id,
                offset=offset,
                limit=batch_limit,
            )
            if not subscribers_batch:
                break

            recipient_records = [
                CampaignRecipient(
                    campaign_id=campaign.id,
                    subscriber_id=sub.id,
                    email=sub.email,
                    tracking_token=secrets.token_urlsafe(32),
                    status=RecipientStatus.PENDING.value,
                    attempts=0,
                )
                for sub in subscribers_batch
            ]
            await recipient_repository.bulk_create(db, recipient_records)
            offset += len(subscribers_batch)

        return active_count

    async def queue_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        """
        Snapshot recipients, transition campaign READY -> QUEUED, and enqueue background Celery execution task.
        """
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        # 1. State Validation
        if campaign.status == CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must be in READY status before sending. Please validate and mark ready first.",
            )

        if campaign.status != CampaignStatus.READY.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign cannot be sent in '{campaign.status.upper()}' status.",
            )

        # 2. Validate Foreign Resources
        await self._validate_foreign_ownership(
            db,
            owner_id=owner_id,
            template_id=campaign.template_id,
            contact_list_id=campaign.contact_list_id,
        )

        # 3. Snapshot Recipients
        await self._snapshot_recipients(db, campaign)

        # 4. Set Status = QUEUED and Commit DB State
        campaign.status = CampaignStatus.QUEUED.value
        await db.commit()
        await db.refresh(campaign)

        # 5. Enqueue Celery Task
        try:
            from app.tasks.campaign_tasks import execute_campaign_task
            execute_campaign_task.delay(str(campaign.id))
        except Exception as exc:
            logger.error(f"Failed to enqueue Celery task for Campaign {campaign.id}: {exc}")
            # Revert to READY and rollback recipients so user can safely retry
            campaign.status = CampaignStatus.READY.value
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Campaign queue broker is temporarily unavailable. Please try again.",
            )

        return campaign

    async def schedule_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
        schedule_in: CampaignScheduleRequest,
    ) -> EmailCampaign:
        """
        Schedule a READY campaign for future asynchronous dispatch.
        Validates timezone, verifies future UTC timestamp, and transitions READY -> SCHEDULED.
        """
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        # 1. State Validation
        if campaign.status == CampaignStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign must be in READY status before scheduling. Please validate and mark ready first.",
            )

        if campaign.status != CampaignStatus.READY.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign cannot be scheduled from '{campaign.status.upper()}' status. Only READY campaigns can be scheduled.",
            )

        # 2. Timezone Validation
        tz_name = (schedule_in.timezone or "UTC").strip()
        try:
            ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, Exception):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone specified: '{tz_name}'. Please provide a valid IANA timezone identifier (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York').",
            )

        # 3. Future Datetime Validation
        target_dt = schedule_in.scheduled_at
        if target_dt.tzinfo is None:
            # If naive, assume user-specified timezone
            user_tz = ZoneInfo(tz_name)
            target_dt = target_dt.replace(tzinfo=user_tz)

        # Normalize to UTC
        target_utc = target_dt.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)

        if target_utc <= now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled datetime must be in the future.",
            )

        # 4. Verify Active Subscribers Exist
        active_count = await subscriber_repository.count_active_subscribers(
            db,
            contact_list_id=campaign.contact_list_id,
        )
        if active_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot schedule campaign: Referenced contact list has no active subscribers.",
            )

        # 5. Transition to SCHEDULED
        campaign.status = CampaignStatus.SCHEDULED.value
        campaign.scheduled_at = target_utc
        campaign.timezone = tz_name

        await db.commit()
        await db.refresh(campaign)
        logger.info(f"Campaign {campaign.id} successfully scheduled for {target_utc.isoformat()} (TZ: {tz_name})")
        return campaign

    async def cancel_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> EmailCampaign:
        """
        Cancel a SCHEDULED, QUEUED, or READY campaign before delivery completes.
        """
        campaign = await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)

        cancellable_statuses = [
            CampaignStatus.READY.value,
            CampaignStatus.SCHEDULED.value,
            CampaignStatus.QUEUED.value,
        ]

        if campaign.status not in cancellable_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel campaign in '{campaign.status.upper()}' status. Only READY, SCHEDULED, or QUEUED campaigns can be cancelled.",
            )

        campaign.status = CampaignStatus.CANCELLED.value
        await db.commit()
        await db.refresh(campaign)
        logger.info(f"Campaign {campaign.id} successfully cancelled by owner {owner_id}.")
        return campaign

    async def trigger_due_scheduled_campaigns(
        self,
        db: AsyncSession,
    ) -> int:
        """
        Triggered periodically by Celery Beat scheduler to locate due SCHEDULED campaigns,
        snapshot recipients, atomically transition status to QUEUED, and enqueue worker tasks.
        """
        now_utc = datetime.now(timezone.utc)
        due_campaigns = await campaign_repository.get_due_scheduled_campaigns(
            db,
            now_utc=now_utc,
            limit=50,
        )

        if not due_campaigns:
            return 0

        triggered_count = 0
        from app.tasks.campaign_tasks import execute_campaign_task

        for campaign in due_campaigns:
            try:
                # 1. Snapshot recipients if not already present
                existing_recipients_count = await recipient_repository.count_unprocessed(db, campaign_id=campaign.id)
                if existing_recipients_count == 0:
                    await self._snapshot_recipients(db, campaign)

                # 2. Transition SCHEDULED -> QUEUED
                campaign.status = CampaignStatus.QUEUED.value
                await db.commit()

                # 3. Enqueue Celery Task
                execute_campaign_task.delay(str(campaign.id))
                triggered_count += 1
                logger.info(f"Scheduled campaign {campaign.id} due at {campaign.scheduled_at} successfully queued.")

            except Exception as exc:
                logger.error(f"Failed to trigger scheduled campaign {campaign.id}: {exc}", exc_info=True)
                await db.rollback()

        return triggered_count

    async def get_campaign_stats(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        owner_id: UUID,
    ) -> CampaignStatsResponse:
        """
        Retrieve database-aggregated stats for a specific campaign.
        """
        await self.get_by_id(db, campaign_id=campaign_id, owner_id=owner_id)
        stats_dict = await recipient_repository.get_campaign_stats(db, campaign_id=campaign_id)
        return CampaignStatsResponse(**stats_dict)


campaign_service = CampaignService()
