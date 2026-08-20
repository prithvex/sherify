from typing import Dict
import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign
from app.models.contact_list import ContactList
from app.models.template import EmailTemplate


@pytest.mark.asyncio
async def test_delete_template_referenced_by_campaign_rejected_api(
    async_client: AsyncClient,
    template_a: EmailTemplate,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """
    Test deleting a template that is referenced by an existing campaign returns 409 Conflict.
    """
    resp = await async_client.delete(f"/api/v1/templates/{template_a.id}", headers=auth_headers_a)
    assert resp.status_code == 409
    assert "referenced by existing campaigns" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_contact_list_referenced_by_campaign_rejected_api(
    async_client: AsyncClient,
    contact_list_a: ContactList,
    campaign_a: EmailCampaign,
    auth_headers_a: Dict[str, str],
):
    """
    Test deleting a contact list that is referenced by an existing campaign returns 409 Conflict.
    """
    resp = await async_client.delete(f"/api/v1/contact-lists/{contact_list_a.id}", headers=auth_headers_a)
    assert resp.status_code == 409
    assert "referenced by existing campaigns" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_db_restrict_template_fk(
    db_session: AsyncSession,
    template_a: EmailTemplate,
    campaign_a: EmailCampaign,
):
    """Test database-level ON DELETE RESTRICT on template_id."""
    await db_session.delete(template_a)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_db_restrict_contact_list_fk(
    db_session: AsyncSession,
    contact_list_a: ContactList,
    campaign_a: EmailCampaign,
):
    """Test database-level ON DELETE RESTRICT on contact_list_id."""
    await db_session.delete(contact_list_a)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
