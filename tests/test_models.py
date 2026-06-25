"""ORM model tests against in-memory SQLite."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.models import Profile, ProfileChannel, ProfileFollow, User


def _make_user(n: int = 1) -> User:
    return User(
        email=f"user{n}@example.com",
        name=f"User {n}",
        google_id=f"google_{n}",
    )


def _make_profile(user: User, n: int = 1) -> Profile:
    return Profile(name=f"Profile {n}", user=user)


async def test_all_tables_in_metadata() -> None:
    assert set(Base.metadata.tables.keys()) == {
        "user",
        "profile",
        "profile_follow",
        "profile_channel",
    }


async def test_create_user(db_session: AsyncSession) -> None:
    user = _make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "user1@example.com"
    assert user.name == "User 1"


async def test_user_profiles_relationship(db_session: AsyncSession) -> None:
    user = _make_user(2)
    _make_profile(user, 1)
    _make_profile(user, 2)
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(Profile).where(Profile.user_id == user.id))
    profiles = result.scalars().all()
    assert len(profiles) == 2
    assert {p.name for p in profiles} == {"Profile 1", "Profile 2"}


async def test_create_profile_follow(db_session: AsyncSession) -> None:
    follower = _make_user(3)
    owner = _make_user(4)
    profile = _make_profile(owner, 1)
    db_session.add_all([follower, owner])
    await db_session.commit()

    follow = ProfileFollow(follower_id=follower.id, profile_id=profile.id)
    db_session.add(follow)
    await db_session.commit()
    await db_session.refresh(follow)

    assert follow.id is not None
    assert follow.follower_id == follower.id
    assert follow.profile_id == profile.id


async def test_create_profile_channel(db_session: AsyncSession) -> None:
    user = _make_user(5)
    profile = _make_profile(user, 1)
    db_session.add(user)
    await db_session.commit()

    channel = ProfileChannel(
        profile_id=profile.id,
        youtube_channel_id="yt_5",
        channel_title="My Channel",
        thumbnail_url="https://example.com/thumb.png",
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    assert channel.id is not None
    assert channel.channel_title == "My Channel"


async def test_cascade_delete_profile_removes_channels(db_session: AsyncSession) -> None:
    user = _make_user(6)
    profile = _make_profile(user, 1)
    db_session.add(user)
    await db_session.commit()

    channel = ProfileChannel(
        profile_id=profile.id,
        youtube_channel_id="yt_6",
        channel_title="Delete Me",
    )
    db_session.add(channel)
    await db_session.commit()
    channel_id = channel.id

    await db_session.delete(profile)
    await db_session.commit()

    result = await db_session.execute(
        select(ProfileChannel).where(ProfileChannel.id == channel_id)
    )
    assert result.scalars().first() is None
