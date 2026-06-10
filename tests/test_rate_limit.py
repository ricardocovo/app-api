"""Integration tests for per-user API rate limiting (100 req/min)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app

RATE_LIMIT_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Non-exempt endpoint used to exercise the rate-limit counter.
# GET /api/v1/users returns 200 with a paginated list and requires no body.
_COUNTED_URL = "/api/v1/users"

# Patch target: replace the `get_remote_address` name in the limiter module so
# that the thin `get_ip_address` wrapper picks up the mock on its next call.
_KEY_PATCH = "app.core.limiter.get_remote_address"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def rl_engine():
    engine = create_async_engine(
        RATE_LIMIT_DATABASE_URL,
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


@pytest.fixture
async def rl_db(rl_engine):
    factory = async_sessionmaker(
        bind=rl_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset the in-memory rate-limit counters before every test."""
    limiter.reset()
    yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_under_limit_all_succeed(rl_db: AsyncSession) -> None:
    """99 requests from the same IP must all return non-429 responses."""

    async def _override_get_db():
        yield rl_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(_KEY_PATCH, return_value="10.0.0.1"):
                for i, _ in enumerate(range(99), start=1):
                    r = await client.get(_COUNTED_URL)
                    assert r.status_code != 429, (
                        f"Request {i} was rate-limited unexpectedly"
                    )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_at_limit_100th_succeeds(rl_db: AsyncSession) -> None:
    """The 100th request must still succeed (limit is inclusive)."""

    async def _override_get_db():
        yield rl_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(_KEY_PATCH, return_value="10.0.0.2"):
                for i, _ in enumerate(range(100), start=1):
                    r = await client.get(_COUNTED_URL)
                    assert r.status_code != 429, (
                        f"Request {i} was rate-limited unexpectedly"
                    )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_over_limit_returns_429(rl_db: AsyncSession) -> None:
    """The 101st request must receive HTTP 429 with a Retry-After header."""

    async def _override_get_db():
        yield rl_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(_KEY_PATCH, return_value="10.0.0.3"):
                # Exhaust the 100-request allowance
                for _ in range(100):
                    await client.get(_COUNTED_URL)

                # The 101st call must be rejected
                r = await client.get(_COUNTED_URL)
                assert r.status_code == 429
                assert "Retry-After" in r.headers
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_different_ips_independent_counters(rl_db: AsyncSession) -> None:
    """Requests from different IPs must have independent rate-limit counters."""

    async def _override_get_db():
        yield rl_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Exhaust the limit for IP A
            with patch(_KEY_PATCH, return_value="10.0.1.1"):
                for _ in range(100):
                    await client.get(_COUNTED_URL)
                r_a = await client.get(_COUNTED_URL)
                assert r_a.status_code == 429, (
                    "IP A should be rate-limited after 101 requests"
                )

            # IP B must still have its own fresh counter
            with patch(_KEY_PATCH, return_value="10.0.1.2"):
                r_b = await client.get(_COUNTED_URL)
                assert r_b.status_code != 429, "IP B should not be rate-limited"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_endpoint_exempt(rl_db: AsyncSession) -> None:
    """Repeated calls to /health must never return 429 regardless of the limit."""

    async def _override_get_db():
        yield rl_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            with patch(_KEY_PATCH, return_value="10.0.2.1"):
                # Send well over the limit exclusively to the exempt /health endpoint
                for i, _ in enumerate(range(150), start=1):
                    r = await client.get("/health")
                    assert r.status_code == 200, (
                        f"Health check {i} returned {r.status_code}"
                    )
    finally:
        app.dependency_overrides.clear()
