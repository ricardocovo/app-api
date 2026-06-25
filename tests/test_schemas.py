"""Unit tests for Pydantic schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.schemas import (
    Page,
    PaginationParams,
    ProfileChannelCreate,
    ProfileChannelRead,
    ProfileChannelUpdate,
    ProfileCreate,
    ProfileFollowCreate,
    ProfileFollowRead,
    ProfileFollowUpdate,
    ProfileRead,
    ProfileUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
UUID_1 = "00000000-0000-0000-0000-000000000001"
UUID_2 = "00000000-0000-0000-0000-000000000002"


def _orm_mock(**attrs) -> MagicMock:
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def test_user_create_valid() -> None:
    user = UserCreate(email="alice@example.com", name="Alice", google_id="g1")
    assert user.email == "alice@example.com"
    assert user.name == "Alice"


def test_user_update_optional_fields() -> None:
    update = UserUpdate()
    assert update.name is None
    assert update.email is None


def test_user_read_from_orm() -> None:
    orm_obj = _orm_mock(
        id=UUID_1,
        email="alice@example.com",
        name="Alice",
        google_id="g1",
        avatar_url=None,
        created_at=NOW,
        updated_at=NOW,
    )
    read = UserRead.model_validate(orm_obj)
    assert str(read.id) == UUID_1
    assert read.email == "alice@example.com"


def test_profile_create_valid() -> None:
    profile = ProfileCreate(user_id=UUID_1, name="Creator", is_default=True, is_public=False)
    assert str(profile.user_id) == UUID_1
    assert profile.name == "Creator"
    assert profile.is_default is True


def test_profile_update_all_optional() -> None:
    update = ProfileUpdate()
    assert update.name is None
    assert update.is_default is None
    assert update.is_public is None


def test_profile_read_from_orm() -> None:
    orm_obj = _orm_mock(
        id=UUID_2,
        user_id=UUID_1,
        name="Profile",
        is_default=False,
        is_public=True,
        created_at=NOW,
        updated_at=NOW,
    )
    read = ProfileRead.model_validate(orm_obj)
    assert str(read.id) == UUID_2
    assert read.name == "Profile"


def test_follow_create_valid() -> None:
    follow = ProfileFollowCreate(follower_id=UUID_1, profile_id=UUID_2)
    assert str(follow.follower_id) == UUID_1
    assert str(follow.profile_id) == UUID_2


def test_follow_update_empty() -> None:
    update = ProfileFollowUpdate()
    assert update.model_dump() == {}


def test_follow_read_from_orm() -> None:
    orm_obj = _orm_mock(id=UUID_2, follower_id=UUID_1, profile_id=UUID_2, created_at=NOW)
    read = ProfileFollowRead.model_validate(orm_obj)
    assert str(read.follower_id) == UUID_1


def test_channel_create_valid() -> None:
    ch = ProfileChannelCreate(
        profile_id=UUID_1,
        youtube_channel_id="yt_123",
        channel_title="My Channel",
        thumbnail_url="https://example.com/t.png",
    )
    assert ch.channel_title == "My Channel"


def test_channel_update_all_optional() -> None:
    update = ProfileChannelUpdate()
    assert update.youtube_channel_id is None
    assert update.channel_title is None
    assert update.thumbnail_url is None


def test_channel_read_from_orm() -> None:
    orm_obj = _orm_mock(
        id=UUID_2,
        profile_id=UUID_1,
        youtube_channel_id="yt_123",
        channel_title="My Channel",
        thumbnail_url=None,
    )
    read = ProfileChannelRead.model_validate(orm_obj)
    assert read.channel_title == "My Channel"


def test_pagination_defaults_and_offset() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.size == 20
    assert params.offset == 0

    params = PaginationParams(page=3, size=10)
    assert params.offset == 20


def test_pagination_bounds() -> None:
    with pytest.raises(Exception):
        PaginationParams(page=0)
    with pytest.raises(Exception):
        PaginationParams(size=101)


def test_page_create() -> None:
    params = PaginationParams(page=2, size=10)
    page = Page.create(items=[1, 2], total=25, params=params)
    assert page.total == 25
    assert page.pages == 3
