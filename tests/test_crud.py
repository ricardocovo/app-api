"""Tests for the CRUD layer (Phase 4/5).

Uses the same in-memory SQLite fixture as other tests.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.profile import create_profile, delete_profile, get_profile, get_profiles, update_profile
from app.crud.profile_channel import (
    create_channel,
    delete_channel,
    get_channel,
    get_channels,
    update_channel,
)
from app.crud.profile_follow import create_follow, delete_follow, get_follow, get_follows
from app.crud.user import create_user, delete_user, get_user, get_users, update_user
from app.schemas.pagination import PaginationParams
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.schemas.profile_channel import ProfileChannelCreate, ProfileChannelUpdate
from app.schemas.profile_follow import ProfileFollowCreate
from app.schemas.user import UserCreate, UserUpdate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_USER_COUNTER = 200  # start high to avoid conflicts with test_models.py


def _next_n() -> int:
    global _USER_COUNTER
    _USER_COUNTER += 1
    return _USER_COUNTER


def _user_create(n: int) -> UserCreate:
    return UserCreate(
        username=f"crud_user{n}",
        email=f"crud_user{n}@example.com",
        password_hash="hashed",
    )


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_get_user(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    assert user.id is not None

    fetched = await get_user(db_session, user.id)
    assert fetched is not None
    assert fetched.username == f"crud_user{n}"


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession) -> None:
    result = await get_user(db_session, 999999)
    assert result is None


@pytest.mark.asyncio
async def test_list_users(db_session: AsyncSession) -> None:
    n1, n2 = _next_n(), _next_n()
    await create_user(db_session, _user_create(n1))
    await create_user(db_session, _user_create(n2))

    items, total = await get_users(db_session, PaginationParams(page=1, size=100))
    assert total >= 2


@pytest.mark.asyncio
async def test_list_users_email_filter(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))

    items, total = await get_users(db_session, PaginationParams(), email=user.email)
    assert total == 1
    assert items[0].id == user.id


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))

    updated = await update_user(db_session, user.id, UserUpdate(username=f"updated_{n}"))
    assert updated is not None
    assert updated.username == f"updated_{n}"


@pytest.mark.asyncio
async def test_update_user_not_found(db_session: AsyncSession) -> None:
    result = await update_user(db_session, 999999, UserUpdate(username="x"))
    assert result is None


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    deleted = await delete_user(db_session, user.id)
    assert deleted is True

    assert await get_user(db_session, user.id) is None


@pytest.mark.asyncio
async def test_delete_user_not_found(db_session: AsyncSession) -> None:
    result = await delete_user(db_session, 999999)
    assert result is False


@pytest.mark.asyncio
async def test_create_user_duplicate_email_raises(db_session: AsyncSession) -> None:
    n = _next_n()
    await create_user(db_session, _user_create(n))
    with pytest.raises(IntegrityError):
        await create_user(db_session, _user_create(n))  # same email


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_get_profile(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name=f"Profile {n}")
    )
    assert profile.id is not None

    fetched = await get_profile(db_session, profile.id)
    assert fetched is not None
    assert fetched.display_name == f"Profile {n}"


@pytest.mark.asyncio
async def test_list_profiles_user_id_filter(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    await create_profile(db_session, ProfileCreate(user_id=user.id, display_name="P1"))
    await create_profile(db_session, ProfileCreate(user_id=user.id, display_name="P2"))

    items, total = await get_profiles(db_session, PaginationParams(), user_id=user.id)
    assert total == 2


@pytest.mark.asyncio
async def test_update_profile(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="Old Name")
    )

    updated = await update_profile(
        db_session, profile.id, ProfileUpdate(display_name="New Name")
    )
    assert updated is not None
    assert updated.display_name == "New Name"


@pytest.mark.asyncio
async def test_delete_profile(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="ToDelete")
    )

    deleted = await delete_profile(db_session, profile.id)
    assert deleted is True
    assert await get_profile(db_session, profile.id) is None


# ---------------------------------------------------------------------------
# ProfileFollow CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_get_follow(db_session: AsyncSession) -> None:
    n1, n2 = _next_n(), _next_n()
    follower = await create_user(db_session, _user_create(n1))
    owner = await create_user(db_session, _user_create(n2))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=owner.id, display_name="Owner Profile")
    )

    follow = await create_follow(
        db_session, ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id)
    )
    assert follow.id is not None

    fetched = await get_follow(db_session, follow.id)
    assert fetched is not None


@pytest.mark.asyncio
async def test_list_follows_with_filters(db_session: AsyncSession) -> None:
    n1, n2 = _next_n(), _next_n()
    follower = await create_user(db_session, _user_create(n1))
    owner = await create_user(db_session, _user_create(n2))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=owner.id, display_name="Prof")
    )
    await create_follow(
        db_session, ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id)
    )

    items, total = await get_follows(
        db_session, PaginationParams(), follower_id=follower.id
    )
    assert total >= 1


@pytest.mark.asyncio
async def test_delete_follow(db_session: AsyncSession) -> None:
    n1, n2 = _next_n(), _next_n()
    follower = await create_user(db_session, _user_create(n1))
    owner = await create_user(db_session, _user_create(n2))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=owner.id, display_name="DelProf")
    )
    follow = await create_follow(
        db_session, ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id)
    )

    deleted = await delete_follow(db_session, follow.id)
    assert deleted is True
    assert await get_follow(db_session, follow.id) is None


# ---------------------------------------------------------------------------
# ProfileChannel CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_get_channel(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="Chan Profile")
    )
    channel = await create_channel(
        db_session,
        ProfileChannelCreate(
            profile_id=profile.id,
            channel_name="YouTube",
            channel_url="https://youtube.com/@example",
        ),
    )
    assert channel.id is not None

    fetched = await get_channel(db_session, channel.id)
    assert fetched is not None
    assert fetched.channel_name == "YouTube"


@pytest.mark.asyncio
async def test_list_channels_profile_filter(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="ChanList Profile")
    )
    await create_channel(
        db_session, ProfileChannelCreate(profile_id=profile.id, channel_name="X")
    )
    await create_channel(
        db_session, ProfileChannelCreate(profile_id=profile.id, channel_name="Y")
    )

    items, total = await get_channels(db_session, PaginationParams(), profile_id=profile.id)
    assert total == 2


@pytest.mark.asyncio
async def test_update_channel(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="UpdChan Profile")
    )
    channel = await create_channel(
        db_session, ProfileChannelCreate(profile_id=profile.id, channel_name="Old")
    )

    updated = await update_channel(
        db_session, channel.id, ProfileChannelUpdate(channel_name="New")
    )
    assert updated is not None
    assert updated.channel_name == "New"


@pytest.mark.asyncio
async def test_delete_channel(db_session: AsyncSession) -> None:
    n = _next_n()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, display_name="DelChan Profile")
    )
    channel = await create_channel(
        db_session, ProfileChannelCreate(profile_id=profile.id, channel_name="ToDelete")
    )

    deleted = await delete_channel(db_session, channel.id)
    assert deleted is True
    assert await get_channel(db_session, channel.id) is None
