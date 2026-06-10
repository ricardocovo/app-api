"""Shared pytest fixtures for the test suite."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from tests.test_utils import create_channel, create_follow, create_profile, create_user

# Use an in-memory SQLite database so tests have no external dependencies.
# StaticPool ensures all connections share a single in-memory database so that
# schema created via create_all() is visible to every session.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create a single async engine for the entire test session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Provide a database session for each test.

    Committed data persists in the shared in-memory database for the full
    test session; tests are responsible for using unique data to avoid
    conflicts.
    """
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


# ============================================================================
# E2E Test Client and Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="module")
async def e2e_engine():
    """Create an async engine for E2E route tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable FK enforcement for SQLite so IntegrityError is raised on bad FKs.
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def e2e_db(e2e_engine):
    """Provide a database session for E2E tests."""
    factory = async_sessionmaker(
        bind=e2e_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(e2e_db: AsyncSession):
    """Provide an AsyncClient with overridden database dependency."""
    async def _override_get_db():
        yield e2e_db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ============================================================================
# Quick Entity Creation Fixtures (for convenience in tests)
# ============================================================================


@pytest_asyncio.fixture
async def make_user(client: AsyncClient):
    """Factory fixture to create users."""
    return lambda **overrides: create_user(client, **overrides)


@pytest_asyncio.fixture
async def make_profile(client: AsyncClient):
    """Factory fixture to create profiles."""
    return lambda user_id, **overrides: create_profile(client, user_id, **overrides)


@pytest_asyncio.fixture
async def make_follow(client: AsyncClient):
    """Factory fixture to create follows."""
    return lambda follower_id, profile_id: create_follow(client, follower_id, profile_id)


@pytest_asyncio.fixture
async def make_channel(client: AsyncClient):
    """Factory fixture to create channels."""
    return lambda profile_id, **overrides: create_channel(client, profile_id, **overrides)
