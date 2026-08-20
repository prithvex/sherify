from typing import AsyncGenerator, Dict
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import Base, ContactList, EmailCampaign, EmailTemplate, Subscriber, User


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def setup_test_schema():
    """
    Ensure schema exists in test database for test session.
    """
    engine = create_async_engine(
        settings.TEST_DATABASE_URL or settings.DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    import asyncio
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
    
    asyncio.run(init_models())
    yield


@pytest.fixture
def test_engine():
    """
    Function-scoped async PostgreSQL engine using NullPool to prevent event loop connection leakage.
    """
    engine = create_async_engine(
        settings.TEST_DATABASE_URL or settings.DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    return engine


@pytest.fixture(autouse=True)
async def clean_database_tables(test_engine):
    """
    Clean all table data before each test to ensure test isolation.
    """
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE email_campaigns, email_templates, subscribers, contact_lists, users RESTART IDENTITY CASCADE;"))
    yield


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Async database session fixture for integration tests.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def async_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Async test client with get_db dependency overridden to use test database.
    """
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def user_a(db_session: AsyncSession) -> User:
    """Create test user A."""
    user = User(
        email="user.a@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_a(user_a: User) -> Dict[str, str]:
    """Generate authorization headers for user A."""
    token = create_access_token({"sub": str(user_a.id), "email": user_a.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_b(db_session: AsyncSession) -> User:
    """Create test user B."""
    user = User(
        email="user.b@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_b(user_b: User) -> Dict[str, str]:
    """Generate authorization headers for user B."""
    token = create_access_token({"sub": str(user_b.id), "email": user_b.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive test user."""
    user = User(
        email="inactive@example.com",
        password_hash=get_password_hash("Password123!"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def inactive_auth_headers(inactive_user: User) -> Dict[str, str]:
    """Generate authorization headers for inactive user."""
    token = create_access_token({"sub": str(inactive_user.id), "email": inactive_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def contact_list_a(db_session: AsyncSession, user_a: User) -> ContactList:
    """Create a contact list owned by user A."""
    cl = ContactList(
        owner_id=user_a.id,
        name="User A VIP List",
        description="VIP customers of User A",
    )
    db_session.add(cl)
    await db_session.commit()
    await db_session.refresh(cl)
    return cl


@pytest.fixture
async def contact_list_b(db_session: AsyncSession, user_b: User) -> ContactList:
    """Create a contact list owned by user B."""
    cl = ContactList(
        owner_id=user_b.id,
        name="User B Leads",
        description="Leads for User B",
    )
    db_session.add(cl)
    await db_session.commit()
    await db_session.refresh(cl)
    return cl


@pytest.fixture
async def template_a(db_session: AsyncSession, user_a: User) -> EmailTemplate:
    """Create an email template owned by user A."""
    template = EmailTemplate(
        owner_id=user_a.id,
        name="Welcome Newsletter",
        subject="Welcome to Sherify!",
        html_content="<h1>Welcome</h1><p>Thanks for joining!</p>",
        text_content="Welcome! Thanks for joining!",
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def template_b(db_session: AsyncSession, user_b: User) -> EmailTemplate:
    """Create an email template owned by user B."""
    template = EmailTemplate(
        owner_id=user_b.id,
        name="User B Promo",
        subject="Special offer from User B",
        html_content="<h1>Special Offer</h1>",
        text_content="Special Offer",
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def campaign_a(
    db_session: AsyncSession,
    user_a: User,
    template_a: EmailTemplate,
    contact_list_a: ContactList,
) -> EmailCampaign:
    """Create an email campaign in DRAFT owned by user A."""
    campaign = EmailCampaign(
        owner_id=user_a.id,
        name="User A Launch Campaign",
        subject="Big Product Launch!",
        template_id=template_a.id,
        contact_list_id=contact_list_a.id,
        status="draft",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign
