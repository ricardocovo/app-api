"""CRUD layer tests."""

from __future__ import annotations

import uuid

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

_CTR = 200


def _next() -> int:
    global _CTR
    _CTR += 1
    return _CTR


def _user_create(n: int) -> UserCreate:
    return UserCreate(
        email=f"crud_user{n}@example.com",
        name=f"Crud User {n}",
        google_id=f"google_{n}",
    )


@pytest.mark.asyncio
async def test_create_and_get_user(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    fetched = await get_user(db_session, user.id)
    assert fetched is not None
    assert fetched.email == f"crud_user{n}@example.com"


@pytest.mark.asyncio
async def test_update_and_delete_user(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    updated = await update_user(db_session, user.id, UserUpdate(name="Updated Name"))
    assert updated is not None
    assert updated.name == "Updated Name"

    deleted = await delete_user(db_session, user.id)
    assert deleted is True
    assert await get_user(db_session, user.id) is None


@pytest.mark.asyncio
async def test_list_users_and_filter(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    items, total = await get_users(db_session, PaginationParams(page=1, size=50), email=user.email)
    assert total == 1
    assert items[0].id == user.id


@pytest.mark.asyncio
async def test_duplicate_user_email_raises(db_session: AsyncSession) -> None:
    n = _next()
    await create_user(db_session, _user_create(n))
    with pytest.raises(IntegrityError):
        await create_user(db_session, _user_create(n))


@pytest.mark.asyncio
async def test_create_update_delete_profile(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(
        db_session, ProfileCreate(user_id=user.id, name=f"Profile {n}")
    )
    fetched = await get_profile(db_session, profile.id)
    assert fetched is not None
    assert fetched.name == f"Profile {n}"

    updated = await update_profile(db_session, profile.id, ProfileUpdate(name="Renamed"))
    assert updated is not None
    assert updated.name == "Renamed"

    deleted = await delete_profile(db_session, profile.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_get_profiles_user_filter(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    await create_profile(db_session, ProfileCreate(user_id=user.id, name="P1"))
    await create_profile(db_session, ProfileCreate(user_id=user.id, name="P2"))
    _, total = await get_profiles(db_session, PaginationParams(), user_id=user.id)
    assert total == 2


@pytest.mark.asyncio
async def test_create_and_delete_follow(db_session: AsyncSession) -> None:
    n1, n2 = _next(), _next()
    follower = await create_user(db_session, _user_create(n1))
    owner = await create_user(db_session, _user_create(n2))
    profile = await create_profile(db_session, ProfileCreate(user_id=owner.id, name="Owner"))

    follow = await create_follow(
        db_session, ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id)
    )
    fetched = await get_follow(db_session, follow.id)
    assert fetched is not None

    deleted = await delete_follow(db_session, follow.id)
    assert deleted is True
    assert await get_follow(db_session, follow.id) is None


@pytest.mark.asyncio
async def test_get_follows_filter(db_session: AsyncSession) -> None:
    n1, n2 = _next(), _next()
    follower = await create_user(db_session, _user_create(n1))
    owner = await create_user(db_session, _user_create(n2))
    profile = await create_profile(db_session, ProfileCreate(user_id=owner.id, name="Owner"))
    await create_follow(
        db_session, ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id)
    )

    _, total = await get_follows(db_session, PaginationParams(), follower_id=follower.id)
    assert total == 1


@pytest.mark.asyncio
async def test_create_update_delete_channel(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(db_session, ProfileCreate(user_id=user.id, name="ChannelOwner"))
    channel = await create_channel(
        db_session,
        ProfileChannelCreate(
            profile_id=profile.id,
            youtube_channel_id=f"yt_{n}",
            channel_title="Original",
            thumbnail_url="https://example.com/old.png",
        ),
    )
    fetched = await get_channel(db_session, channel.id)
    assert fetched is not None
    assert fetched.channel_title == "Original"

    updated = await update_channel(
        db_session,
        channel.id,
        ProfileChannelUpdate(channel_title="Updated", thumbnail_url="https://example.com/new.png"),
    )
    assert updated is not None
    assert updated.channel_title == "Updated"

    deleted = await delete_channel(db_session, channel.id)
    assert deleted is True
    assert await get_channel(db_session, channel.id) is None


@pytest.mark.asyncio
async def test_get_channels_profile_filter(db_session: AsyncSession) -> None:
    n = _next()
    user = await create_user(db_session, _user_create(n))
    profile = await create_profile(db_session, ProfileCreate(user_id=user.id, name="ChannelFilter"))
    await create_channel(
        db_session,
        ProfileChannelCreate(profile_id=profile.id, youtube_channel_id="yt_1", channel_title="A"),
    )
    await create_channel(
        db_session,
        ProfileChannelCreate(profile_id=profile.id, youtube_channel_id="yt_2", channel_title="B"),
    )
    _, total = await get_channels(db_session, PaginationParams(), profile_id=profile.id)
    assert total == 2


@pytest.mark.asyncio
async def test_not_found_cases(db_session: AsyncSession) -> None:
    missing = uuid.uuid4()
    assert await get_user(db_session, missing) is None
    assert await update_user(db_session, missing, UserUpdate(name="x")) is None
    assert await delete_user(db_session, missing) is False
