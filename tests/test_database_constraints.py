import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contact_list import ContactList
from app.models.subscriber import Subscriber
from app.models.user import User


@pytest.mark.asyncio
async def test_foreign_key_invalid_user_id(db_session: AsyncSession):
    """Test that creating a contact list with non-existent owner_id raises IntegrityError."""
    cl = ContactList(
        owner_id=uuid.uuid4(),
        name="Orphan List",
    )
    db_session.add(cl)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_foreign_key_invalid_contact_list_id(db_session: AsyncSession):
    """Test that creating a subscriber with non-existent contact_list_id raises IntegrityError."""
    sub = Subscriber(
        contact_list_id=uuid.uuid4(),
        email="orphan@example.com",
    )
    db_session.add(sub)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_db_unique_constraint_subscriber_per_list(
    db_session: AsyncSession,
    contact_list_a: ContactList,
):
    """Test database-level unique constraint on (contact_list_id, email)."""
    sub1 = Subscriber(
        contact_list_id=contact_list_a.id,
        email="unique_check@example.com",
    )
    sub2 = Subscriber(
        contact_list_id=contact_list_a.id,
        email="unique_check@example.com",
    )
    db_session.add(sub1)
    await db_session.commit()

    db_session.add(sub2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cascade_delete_user(
    db_session: AsyncSession,
    user_a: User,
    contact_list_a: ContactList,
):
    """
    Test cascade delete: Deleting a User cascades and deletes their ContactLists and Subscribers.
    """
    sub = Subscriber(
        contact_list_id=contact_list_a.id,
        email="cascade_sub@example.com",
    )
    db_session.add(sub)
    await db_session.commit()

    # Verify entities exist
    res_cl = await db_session.execute(select(ContactList).where(ContactList.id == contact_list_a.id))
    assert res_cl.scalar_one_or_none() is not None

    res_sub = await db_session.execute(select(Subscriber).where(Subscriber.id == sub.id))
    assert res_sub.scalar_one_or_none() is not None

    # Delete User
    await db_session.delete(user_a)
    await db_session.commit()

    # Verify cascaded deletion
    res_cl_after = await db_session.execute(select(ContactList).where(ContactList.id == contact_list_a.id))
    assert res_cl_after.scalar_one_or_none() is None

    res_sub_after = await db_session.execute(select(Subscriber).where(Subscriber.id == sub.id))
    assert res_sub_after.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cascade_delete_contact_list(
    db_session: AsyncSession,
    contact_list_a: ContactList,
):
    """
    Test cascade delete: Deleting a ContactList cascades and deletes all its Subscribers.
    """
    sub1 = Subscriber(contact_list_id=contact_list_a.id, email="sub1@example.com")
    sub2 = Subscriber(contact_list_id=contact_list_a.id, email="sub2@example.com")
    db_session.add_all([sub1, sub2])
    await db_session.commit()

    # Delete Contact List
    await db_session.delete(contact_list_a)
    await db_session.commit()

    # Verify Subscribers were deleted
    res_subs = await db_session.execute(
        select(Subscriber).where(Subscriber.contact_list_id == contact_list_a.id)
    )
    assert len(list(res_subs.scalars().all())) == 0
