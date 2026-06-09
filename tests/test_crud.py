"""Tests for the Phase-4 async CRUD layer.

All tests use the same in-memory SQLite database as the model tests (see
``conftest.py``).  Each test uses unique data to avoid conflicts with data
committed by other tests in the shared session-scoped database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    profile_channel_crud,
    profile_crud,
    profile_follow_crud,
    user_crud,
)
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.schemas.profile_channel import ProfileChannelCreate, ProfileChannelUpdate
from app.schemas.profile_follow import ProfileFollowCreate
from app.schemas.user import UserCreate, UserUpdate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COUNTER: dict[str, int] = {"n": 100}


def _next() -> int:
    _COUNTER["n"] += 1
    return _COUNTER["n"]


def _user_in(n: int | None = None) -> UserCreate:
    n = n or _next()
    return UserCreate(
        username=f"crud_user{n}",
        email=f"crud_user{n}@example.com",
        password_hash="hashed",
    )


# ---------------------------------------------------------------------------
# CRUDUser
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_create_and_get(db_session: AsyncSession) -> None:
    obj_in = _user_in()
    user = await user_crud.create(db_session, obj_in=obj_in)

    assert user.id is not None
    assert user.username == obj_in.username

    fetched = await user_crud.get(db_session, user.id)
    assert fetched is not None
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_user_get_returns_none_for_missing(db_session: AsyncSession) -> None:
    result = await user_crud.get(db_session, 999_999)
    assert result is None


@pytest.mark.asyncio
async def test_user_get_multi_pagination_and_total(db_session: AsyncSession) -> None:
    n = _next()
    # Create 3 users with recognisable usernames
    for i in range(3):
        await user_crud.create(
            db_session,
            obj_in=UserCreate(
                username=f"pag_user{n}_{i}",
                email=f"pag_user{n}_{i}@example.com",
                password_hash="hashed",
            ),
        )

    rows, total = await user_crud.get_multi(db_session, offset=0, limit=1000)
    assert total >= 3
    assert len(rows) >= 3


@pytest.mark.asyncio
async def test_user_update_partial(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    original_email = user.email

    updated = await user_crud.update(
        db_session,
        db_obj=user,
        obj_in=UserUpdate(username="updated_name"),
    )

    assert updated.username == "updated_name"
    assert updated.email == original_email  # unchanged


@pytest.mark.asyncio
async def test_user_delete(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    uid = user.id

    deleted = await user_crud.delete(db_session, id=uid)
    assert deleted is not None
    assert deleted.id == uid

    assert await user_crud.get(db_session, uid) is None


@pytest.mark.asyncio
async def test_user_delete_nonexistent_returns_none(db_session: AsyncSession) -> None:
    result = await user_crud.delete(db_session, id=999_998)
    assert result is None


@pytest.mark.asyncio
async def test_user_get_by_email(db_session: AsyncSession) -> None:
    obj_in = _user_in()
    await user_crud.create(db_session, obj_in=obj_in)

    found = await user_crud.get_by_email(db_session, obj_in.email)
    assert found is not None
    assert found.email == obj_in.email

    not_found = await user_crud.get_by_email(db_session, "no_such@example.com")
    assert not_found is None


@pytest.mark.asyncio
async def test_user_get_by_username(db_session: AsyncSession) -> None:
    obj_in = _user_in()
    await user_crud.create(db_session, obj_in=obj_in)

    found = await user_crud.get_by_username(db_session, obj_in.username)
    assert found is not None
    assert found.username == obj_in.username

    not_found = await user_crud.get_by_username(db_session, "no_such_user")
    assert not_found is None


# ---------------------------------------------------------------------------
# CRUDProfile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_create_and_get(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    obj_in = ProfileCreate(display_name="Test Profile", user_id=user.id)

    profile = await profile_crud.create(db_session, obj_in=obj_in)
    assert profile.id is not None
    assert profile.user_id == user.id

    fetched = await profile_crud.get(db_session, profile.id)
    assert fetched is not None
    assert fetched.display_name == "Test Profile"


@pytest.mark.asyncio
async def test_profile_update_partial(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="Old Name", user_id=user.id)
    )

    updated = await profile_crud.update(
        db_session,
        db_obj=profile,
        obj_in=ProfileUpdate(display_name="New Name"),
    )
    assert updated.display_name == "New Name"
    assert updated.bio is None  # unchanged


@pytest.mark.asyncio
async def test_profile_delete(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="To Delete", user_id=user.id)
    )
    pid = profile.id

    deleted = await profile_crud.delete(db_session, id=pid)
    assert deleted is not None
    assert await profile_crud.get(db_session, pid) is None


@pytest.mark.asyncio
async def test_profile_get_by_user(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    for i in range(3):
        await profile_crud.create(
            db_session,
            obj_in=ProfileCreate(display_name=f"Profile {i}", user_id=user.id),
        )

    rows, total = await profile_crud.get_by_user(db_session, user.id)
    assert total == 3
    assert len(rows) == 3
    assert all(p.user_id == user.id for p in rows)


@pytest.mark.asyncio
async def test_profile_get_multi_filter(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="Filtered", user_id=user.id)
    )

    rows, total = await profile_crud.get_multi(
        db_session, filters={"user_id": user.id}
    )
    assert total >= 1
    assert all(p.user_id == user.id for p in rows)


# ---------------------------------------------------------------------------
# CRUDProfileFollow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_follow_create_and_get(db_session: AsyncSession) -> None:
    follower = await user_crud.create(db_session, obj_in=_user_in())
    owner = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="FollowMe", user_id=owner.id)
    )

    follow = await profile_follow_crud.create(
        db_session,
        obj_in=ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id),
    )
    assert follow.id is not None

    fetched = await profile_follow_crud.get(db_session, follow.id)
    assert fetched is not None
    assert fetched.follower_id == follower.id
    assert fetched.profile_id == profile.id


@pytest.mark.asyncio
async def test_profile_follow_get_by_follower(db_session: AsyncSession) -> None:
    follower = await user_crud.create(db_session, obj_in=_user_in())
    owner = await user_crud.create(db_session, obj_in=_user_in())
    for i in range(2):
        profile = await profile_crud.create(
            db_session,
            obj_in=ProfileCreate(display_name=f"P{i}", user_id=owner.id),
        )
        await profile_follow_crud.create(
            db_session,
            obj_in=ProfileFollowCreate(
                follower_id=follower.id, profile_id=profile.id
            ),
        )

    rows, total = await profile_follow_crud.get_by_follower(db_session, follower.id)
    assert total == 2
    assert all(f.follower_id == follower.id for f in rows)


@pytest.mark.asyncio
async def test_profile_follow_get_by_profile(db_session: AsyncSession) -> None:
    owner = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="Popular", user_id=owner.id)
    )
    for _ in range(2):
        follower = await user_crud.create(db_session, obj_in=_user_in())
        await profile_follow_crud.create(
            db_session,
            obj_in=ProfileFollowCreate(
                follower_id=follower.id, profile_id=profile.id
            ),
        )

    rows, total = await profile_follow_crud.get_by_profile(db_session, profile.id)
    assert total == 2
    assert all(f.profile_id == profile.id for f in rows)


@pytest.mark.asyncio
async def test_profile_follow_get_by_follower_and_profile(
    db_session: AsyncSession,
) -> None:
    follower = await user_crud.create(db_session, obj_in=_user_in())
    owner = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="Specific", user_id=owner.id)
    )
    await profile_follow_crud.create(
        db_session,
        obj_in=ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id),
    )

    found = await profile_follow_crud.get_by_follower_and_profile(
        db_session, follower.id, profile.id
    )
    assert found is not None

    not_found = await profile_follow_crud.get_by_follower_and_profile(
        db_session, follower.id, 999_997
    )
    assert not_found is None


@pytest.mark.asyncio
async def test_profile_follow_delete(db_session: AsyncSession) -> None:
    follower = await user_crud.create(db_session, obj_in=_user_in())
    owner = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="DelFollow", user_id=owner.id)
    )
    follow = await profile_follow_crud.create(
        db_session,
        obj_in=ProfileFollowCreate(follower_id=follower.id, profile_id=profile.id),
    )
    fid = follow.id

    deleted = await profile_follow_crud.delete(db_session, id=fid)
    assert deleted is not None
    assert await profile_follow_crud.get(db_session, fid) is None


# ---------------------------------------------------------------------------
# CRUDProfileChannel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_channel_create_and_get(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session, obj_in=ProfileCreate(display_name="Chan Profile", user_id=user.id)
    )

    channel = await profile_channel_crud.create(
        db_session,
        obj_in=ProfileChannelCreate(
            channel_name="Twitter",
            channel_url="https://twitter.com/example",
            profile_id=profile.id,
        ),
    )
    assert channel.id is not None

    fetched = await profile_channel_crud.get(db_session, channel.id)
    assert fetched is not None
    assert fetched.channel_name == "Twitter"


@pytest.mark.asyncio
async def test_profile_channel_update_partial(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session,
        obj_in=ProfileCreate(display_name="Chan Profile 2", user_id=user.id),
    )
    channel = await profile_channel_crud.create(
        db_session,
        obj_in=ProfileChannelCreate(
            channel_name="OldName",
            profile_id=profile.id,
        ),
    )

    updated = await profile_channel_crud.update(
        db_session,
        db_obj=channel,
        obj_in=ProfileChannelUpdate(channel_name="NewName"),
    )
    assert updated.channel_name == "NewName"
    assert updated.channel_url is None  # unchanged


@pytest.mark.asyncio
async def test_profile_channel_get_by_profile(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session,
        obj_in=ProfileCreate(display_name="Multi Chan", user_id=user.id),
    )
    for i in range(3):
        await profile_channel_crud.create(
            db_session,
            obj_in=ProfileChannelCreate(
                channel_name=f"Chan{i}", profile_id=profile.id
            ),
        )

    rows, total = await profile_channel_crud.get_by_profile(db_session, profile.id)
    assert total == 3
    assert all(c.profile_id == profile.id for c in rows)


@pytest.mark.asyncio
async def test_profile_channel_delete(db_session: AsyncSession) -> None:
    user = await user_crud.create(db_session, obj_in=_user_in())
    profile = await profile_crud.create(
        db_session,
        obj_in=ProfileCreate(display_name="Del Chan Profile", user_id=user.id),
    )
    channel = await profile_channel_crud.create(
        db_session,
        obj_in=ProfileChannelCreate(channel_name="ToDelete", profile_id=profile.id),
    )
    cid = channel.id

    deleted = await profile_channel_crud.delete(db_session, id=cid)
    assert deleted is not None
    assert await profile_channel_crud.get(db_session, cid) is None
