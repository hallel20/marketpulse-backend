"""
Pytest configuration and fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_async_session, Base
from app.config import get_settings
from app.models.user import User
from app.services.auth_service import AuthService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

test_async_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with test_async_session_maker() as session:
        try:
            yield session
        finally:
            pass
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database session override"""
    
    async def get_test_session():
        yield async_session
    
    app.dependency_overrides[get_async_session] = get_test_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> User:
    """Create a test user"""
    auth_service = AuthService()
    
    user = User(
        email="test@example.com",
        password_hash=auth_service.get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True
    )
    
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def admin_user(async_session: AsyncSession) -> User:
    """Create a test admin user"""
    auth_service = AuthService()
    
    user = User(
        email="admin@example.com",
        password_hash=auth_service.get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_verified=True,
        is_admin=True
    )
    
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user"""
    auth_service = AuthService()
    access_token = auth_service.create_access_token(
        {"sub": test_user.email, "user_id": str(test_user.id)}
    )
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict:
    """Create authentication headers for admin user"""
    auth_service = AuthService()
    access_token = auth_service.create_access_token(
        {"sub": admin_user.email, "user_id": str(admin_user.id)}
    )
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()