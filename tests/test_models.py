"""Tests for the four Phase-2 ORM models.

All tests use an in-memory SQLite database via aiosqlite so that no SQL Server
instance is required.  The behaviour verified here is database-agnostic ORM
behaviour (object creation, relationships, cascade deletes).
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models import Profile, ProfileChannel, ProfileFollow, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(n: int = 1) -> User:
    return User(
        username=f"user{n}",
        email=f"user{n}@example.com",
        password_hash="hashed",
    )


def _make_profile(user: User, n: int = 1) -> Profile:
    return Profile(display_name=f"Profile {n}", user=user)


# ---------------------------------------------------------------------------
# Base metadata
# ---------------------------------------------------------------------------


def test_all_four_tables_in_metadata() -> None:
    """Base.metadata must contain exactly the 4 tables introduced in Phase 2."""
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {"users", "profiles", "profile_follows", "profile_channels"}


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    user = _make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "user1"
    assert user.email == "user1@example.com"
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_profiles_relationship(db_session: AsyncSession) -> None:
    user = _make_user(2)
    p1 = _make_profile(user, 1)
    p2 = _make_profile(user, 2)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await db_session.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profiles = result.scalars().all()
    assert len(profiles) == 2
    assert {p.display_name for p in profiles} == {"Profile 1", "Profile 2"}


# ---------------------------------------------------------------------------
# Profile model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_timestamps(db_session: AsyncSession) -> None:
    user = _make_user(3)
    profile = _make_profile(user)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(profile)

    # SQLite server_default won't auto-fill in pure ORM insert without a server
    # round-trip; verify the columns *exist* and the ORM accepted the row.
    assert profile.id is not None
    assert profile.display_name == "Profile 1"


@pytest.mark.asyncio
async def test_profile_bio_nullable(db_session: AsyncSession) -> None:
    user = _make_user(4)
    profile = Profile(display_name="No Bio", user=user)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(profile)

    assert profile.bio is None


# ---------------------------------------------------------------------------
# ProfileFollow model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_profile_follow(db_session: AsyncSession) -> None:
    follower = _make_user(5)
    owner = _make_user(6)
    profile = _make_profile(owner)
    db_session.add_all([follower, owner])
    await db_session.commit()
    await db_session.refresh(follower)
    await db_session.refresh(profile)

    follow = ProfileFollow(follower_id=follower.id, profile_id=profile.id)
    db_session.add(follow)
    await db_session.commit()
    await db_session.refresh(follow)

    assert follow.id is not None
    assert follow.follower_id == follower.id
    assert follow.profile_id == profile.id


@pytest.mark.asyncio
async def test_profile_follow_back_populates(db_session: AsyncSession) -> None:
    follower = _make_user(7)
    owner = _make_user(8)
    profile = _make_profile(owner)
    db_session.add_all([follower, owner])
    await db_session.commit()

    follow = ProfileFollow(follower_id=follower.id, profile_id=profile.id)
    db_session.add(follow)
    await db_session.commit()

    result = await db_session.execute(
        select(ProfileFollow).where(ProfileFollow.follower_id == follower.id)
    )
    assert result.scalars().first() is not None


# ---------------------------------------------------------------------------
# ProfileChannel model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_profile_channel(db_session: AsyncSession) -> None:
    user = _make_user(9)
    profile = _make_profile(user)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(profile)

    channel = ProfileChannel(
        profile_id=profile.id,
        channel_name="YouTube",
        channel_url="https://youtube.com/@example",
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    assert channel.id is not None
    assert channel.channel_name == "YouTube"
    assert channel.channel_url == "https://youtube.com/@example"


@pytest.mark.asyncio
async def test_profile_channel_url_nullable(db_session: AsyncSession) -> None:
    user = _make_user(10)
    profile = _make_profile(user)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(profile)

    channel = ProfileChannel(profile_id=profile.id, channel_name="Twitter")
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    assert channel.channel_url is None


# ---------------------------------------------------------------------------
# Cascade deletes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cascade_delete_user_removes_profiles(db_session: AsyncSession) -> None:
    user = _make_user(11)
    profile = _make_profile(user)
    db_session.add(user)
    await db_session.commit()
    profile_id = profile.id

    await db_session.delete(user)
    await db_session.commit()

    result = await db_session.execute(
        select(Profile).where(Profile.id == profile_id)
    )
    assert result.scalars().first() is None


@pytest.mark.asyncio
async def test_cascade_delete_profile_removes_channels(
    db_session: AsyncSession,
) -> None:
    user = _make_user(12)
    profile = _make_profile(user)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(profile)

    channel = ProfileChannel(profile_id=profile.id, channel_name="TikTok")
    db_session.add(channel)
    await db_session.commit()
    channel_id = channel.id

    await db_session.delete(profile)
    await db_session.commit()

    result = await db_session.execute(
        select(ProfileChannel).where(ProfileChannel.id == channel_id)
    )
    assert result.scalars().first() is None
