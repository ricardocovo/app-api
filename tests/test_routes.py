"""Integration tests for the Phase-5 API routes.

Uses FastAPI's async test client with an overridden in-memory SQLite DB.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

ROUTE_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def route_engine():
    engine = create_async_engine(
        ROUTE_TEST_DATABASE_URL,
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
async def route_db(route_engine):
    factory = async_sessionmaker(
        bind=route_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(route_db: AsyncSession):
    async def _override_get_db():
        yield route_db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health check (smoke test)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

_ROUTE_CTR = 1000


def _next() -> int:
    global _ROUTE_CTR
    _ROUTE_CTR += 1
    return _ROUTE_CTR


@pytest.mark.asyncio
async def test_create_user_201(client: AsyncClient) -> None:
    n = _next()
    r = await client.post(
        "/api/v1/users",
        json={"username": f"rt_user{n}", "email": f"rt{n}@example.com", "password_hash": "h"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == f"rt_user{n}"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_409(client: AsyncClient) -> None:
    n = _next()
    payload = {"username": f"dup_user{n}", "email": f"dup{n}@example.com", "password_hash": "h"}
    await client.post("/api/v1/users", json=payload)
    r = await client.post("/api/v1/users", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_user_200(client: AsyncClient) -> None:
    n = _next()
    create_r = await client.post(
        "/api/v1/users",
        json={"username": f"get_user{n}", "email": f"get{n}@example.com", "password_hash": "h"},
    )
    user_id = create_r.json()["id"]
    r = await client.get(f"/api/v1/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/users/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient) -> None:
    r = await client.get("/api/v1/users?page=1&size=5")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert "pages" in body


@pytest.mark.asyncio
async def test_patch_user_200(client: AsyncClient) -> None:
    n = _next()
    create_r = await client.post(
        "/api/v1/users",
        json={"username": f"patch_user{n}", "email": f"patch{n}@example.com", "password_hash": "h"},
    )
    user_id = create_r.json()["id"]
    r = await client.patch(f"/api/v1/users/{user_id}", json={"username": f"patched_{n}"})
    assert r.status_code == 200
    assert r.json()["username"] == f"patched_{n}"


@pytest.mark.asyncio
async def test_patch_user_404(client: AsyncClient) -> None:
    r = await client.patch("/api/v1/users/999999", json={"username": "x"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_204(client: AsyncClient) -> None:
    n = _next()
    create_r = await client.post(
        "/api/v1/users",
        json={"username": f"del_user{n}", "email": f"del{n}@example.com", "password_hash": "h"},
    )
    user_id = create_r.json()["id"]
    r = await client.delete(f"/api/v1/users/{user_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_404(client: AsyncClient) -> None:
    r = await client.delete("/api/v1/users/999999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


async def _make_user(client: AsyncClient) -> dict:
    n = _next()
    r = await client.post(
        "/api/v1/users",
        json={"username": f"prof_owner{n}", "email": f"prof_owner{n}@example.com", "password_hash": "h"},
    )
    return r.json()


@pytest.mark.asyncio
async def test_create_profile_201(client: AsyncClient) -> None:
    user = await _make_user(client)
    r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "Test Profile"},
    )
    assert r.status_code == 201
    assert r.json()["display_name"] == "Test Profile"


@pytest.mark.asyncio
async def test_create_profile_invalid_fk_409(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/profiles",
        json={"user_id": 999999, "display_name": "Ghost"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_profile_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/profiles/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_profiles(client: AsyncClient) -> None:
    r = await client.get("/api/v1/profiles?page=1&size=10")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_patch_profile(client: AsyncClient) -> None:
    user = await _make_user(client)
    create_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "Old"},
    )
    pid = create_r.json()["id"]
    r = await client.patch(f"/api/v1/profiles/{pid}", json={"display_name": "New"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "New"


@pytest.mark.asyncio
async def test_delete_profile_204(client: AsyncClient) -> None:
    user = await _make_user(client)
    create_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "DelMe"},
    )
    pid = create_r.json()["id"]
    r = await client.delete(f"/api/v1/profiles/{pid}")
    assert r.status_code == 204


# ---------------------------------------------------------------------------
# Follows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_follow_201(client: AsyncClient) -> None:
    follower = await _make_user(client)
    owner = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": owner["id"], "display_name": "Followable"},
    )
    profile_id = prof_r.json()["id"]

    r = await client.post(
        "/api/v1/follows",
        json={"follower_id": follower["id"], "profile_id": profile_id},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_create_follow_duplicate_409(client: AsyncClient) -> None:
    follower = await _make_user(client)
    owner = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": owner["id"], "display_name": "FollowDup"},
    )
    profile_id = prof_r.json()["id"]
    payload = {"follower_id": follower["id"], "profile_id": profile_id}
    await client.post("/api/v1/follows", json=payload)
    r = await client.post("/api/v1/follows", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_follow_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/follows/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_follow_204(client: AsyncClient) -> None:
    follower = await _make_user(client)
    owner = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": owner["id"], "display_name": "FollowDel"},
    )
    profile_id = prof_r.json()["id"]
    follow_r = await client.post(
        "/api/v1/follows",
        json={"follower_id": follower["id"], "profile_id": profile_id},
    )
    follow_id = follow_r.json()["id"]
    r = await client.delete(f"/api/v1/follows/{follow_id}")
    assert r.status_code == 204


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_channel_201(client: AsyncClient) -> None:
    user = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "Chan Owner"},
    )
    profile_id = prof_r.json()["id"]

    r = await client.post(
        "/api/v1/channels",
        json={"profile_id": profile_id, "channel_name": "YouTube"},
    )
    assert r.status_code == 201
    assert r.json()["channel_name"] == "YouTube"


@pytest.mark.asyncio
async def test_create_channel_invalid_fk_409(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/channels",
        json={"profile_id": 999999, "channel_name": "Ghost"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_channel_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/channels/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_channels(client: AsyncClient) -> None:
    r = await client.get("/api/v1/channels?page=1&size=10")
    assert r.status_code == 200
    assert "items" in r.json()


@pytest.mark.asyncio
async def test_patch_channel(client: AsyncClient) -> None:
    user = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "PatchChan Owner"},
    )
    profile_id = prof_r.json()["id"]
    chan_r = await client.post(
        "/api/v1/channels",
        json={"profile_id": profile_id, "channel_name": "OldName"},
    )
    channel_id = chan_r.json()["id"]

    r = await client.patch(f"/api/v1/channels/{channel_id}", json={"channel_name": "NewName"})
    assert r.status_code == 200
    assert r.json()["channel_name"] == "NewName"


@pytest.mark.asyncio
async def test_delete_channel_204(client: AsyncClient) -> None:
    user = await _make_user(client)
    prof_r = await client.post(
        "/api/v1/profiles",
        json={"user_id": user["id"], "display_name": "DelChan Owner"},
    )
    profile_id = prof_r.json()["id"]
    chan_r = await client.post(
        "/api/v1/channels",
        json={"profile_id": profile_id, "channel_name": "DelChan"},
    )
    channel_id = chan_r.json()["id"]

    r = await client.delete(f"/api/v1/channels/{channel_id}")
    assert r.status_code == 204
