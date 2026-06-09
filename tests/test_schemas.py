"""Unit tests for Phase-3 Pydantic v2 schemas.

Tests cover:
- Clean imports (no circular dependency errors)
- Field validation (required fields, optional defaults)
- ORM-mode serialisation via ``from_attributes=True``
- Pagination helpers
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _orm_mock(**attrs) -> MagicMock:
    """Return a MagicMock that behaves like an ORM instance."""
    mock = MagicMock()
    for k, v in attrs.items():
        setattr(mock, k, v)
    return mock


# ---------------------------------------------------------------------------
# UserCreate
# ---------------------------------------------------------------------------


class TestUserCreate:
    def test_valid_creation(self) -> None:
        user = UserCreate(
            username="alice",
            email="alice@example.com",
            password_hash="hashed_pw",
        )
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password_hash == "hashed_pw"

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(Exception):
            UserCreate(username="bob", email="not-an-email", password_hash="x")

    def test_missing_password_hash_raises(self) -> None:
        with pytest.raises(Exception):
            UserCreate(username="bob", email="bob@example.com")


# ---------------------------------------------------------------------------
# UserUpdate
# ---------------------------------------------------------------------------


class TestUserUpdate:
    def test_all_fields_optional(self) -> None:
        update = UserUpdate()
        assert update.username is None
        assert update.email is None
        assert update.password_hash is None

    def test_partial_update(self) -> None:
        update = UserUpdate(username="new_name")
        assert update.username == "new_name"
        assert update.email is None


# ---------------------------------------------------------------------------
# UserRead (ORM mode)
# ---------------------------------------------------------------------------


class TestUserRead:
    def test_from_orm_instance(self) -> None:
        orm_obj = _orm_mock(
            id=1,
            username="alice",
            email="alice@example.com",
            created_at=NOW,
        )
        read = UserRead.model_validate(orm_obj)
        assert read.id == 1
        assert read.username == "alice"
        assert read.email == "alice@example.com"
        assert read.created_at == NOW

    def test_password_hash_not_in_schema(self) -> None:
        """UserRead must not expose password_hash."""
        assert not hasattr(UserRead.model_fields.get("password_hash"), "default")
        assert "password_hash" not in UserRead.model_fields


# ---------------------------------------------------------------------------
# ProfileCreate / ProfileUpdate / ProfileRead
# ---------------------------------------------------------------------------


class TestProfileCreate:
    def test_valid(self) -> None:
        schema = ProfileCreate(user_id=1, display_name="Alice", bio="Hello")
        assert schema.user_id == 1
        assert schema.bio == "Hello"

    def test_bio_defaults_to_none(self) -> None:
        schema = ProfileCreate(user_id=1, display_name="Alice")
        assert schema.bio is None

    def test_missing_user_id_raises(self) -> None:
        with pytest.raises(Exception):
            ProfileCreate(display_name="Alice")


class TestProfileUpdate:
    def test_all_optional(self) -> None:
        update = ProfileUpdate()
        assert update.display_name is None
        assert update.bio is None


class TestProfileRead:
    def test_from_orm(self) -> None:
        orm_obj = _orm_mock(
            id=5,
            user_id=1,
            display_name="Alice",
            bio="Hello",
            created_at=NOW,
            updated_at=NOW,
        )
        read = ProfileRead.model_validate(orm_obj)
        assert read.id == 5
        assert read.user_id == 1
        assert read.display_name == "Alice"


# ---------------------------------------------------------------------------
# ProfileFollowCreate / ProfileFollowRead
# ---------------------------------------------------------------------------


class TestProfileFollowCreate:
    def test_valid(self) -> None:
        schema = ProfileFollowCreate(follower_id=1, profile_id=2)
        assert schema.follower_id == 1
        assert schema.profile_id == 2

    def test_missing_field_raises(self) -> None:
        with pytest.raises(Exception):
            ProfileFollowCreate(follower_id=1)


class TestProfileFollowUpdate:
    def test_empty_model(self) -> None:
        update = ProfileFollowUpdate()
        assert update.model_dump() == {}


class TestProfileFollowRead:
    def test_from_orm(self) -> None:
        orm_obj = _orm_mock(id=10, follower_id=1, profile_id=2, created_at=NOW)
        read = ProfileFollowRead.model_validate(orm_obj)
        assert read.id == 10
        assert read.follower_id == 1
        assert read.profile_id == 2
        assert read.created_at == NOW


# ---------------------------------------------------------------------------
# ProfileChannelCreate / ProfileChannelUpdate / ProfileChannelRead
# ---------------------------------------------------------------------------


class TestProfileChannelCreate:
    def test_valid_with_url(self) -> None:
        schema = ProfileChannelCreate(
            profile_id=3,
            channel_name="YouTube",
            channel_url="https://youtube.com/@example",
        )
        assert schema.profile_id == 3
        assert schema.channel_name == "YouTube"
        assert schema.channel_url is not None

    def test_url_optional(self) -> None:
        schema = ProfileChannelCreate(profile_id=3, channel_name="Twitter")
        assert schema.channel_url is None

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(Exception):
            ProfileChannelCreate(
                profile_id=3,
                channel_name="Bad",
                channel_url="not-a-url",
            )


class TestProfileChannelUpdate:
    def test_all_optional(self) -> None:
        update = ProfileChannelUpdate()
        assert update.channel_name is None
        assert update.channel_url is None


class TestProfileChannelRead:
    def test_from_orm(self) -> None:
        orm_obj = _orm_mock(
            id=7,
            profile_id=3,
            channel_name="YouTube",
            channel_url="https://youtube.com/@example",
            created_at=NOW,
            updated_at=NOW,
        )
        read = ProfileChannelRead.model_validate(orm_obj)
        assert read.id == 7
        assert read.profile_id == 3
        assert read.channel_name == "YouTube"


# ---------------------------------------------------------------------------
# PaginationParams
# ---------------------------------------------------------------------------


class TestPaginationParams:
    def test_defaults(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0

    def test_offset_calculation(self) -> None:
        params = PaginationParams(page=3, size=10)
        assert params.offset == 20

    def test_page_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            PaginationParams(page=0)

    def test_size_max_100(self) -> None:
        with pytest.raises(Exception):
            PaginationParams(size=101)


# ---------------------------------------------------------------------------
# Page generic wrapper
# ---------------------------------------------------------------------------


class TestPage:
    def test_create_single_page(self) -> None:
        params = PaginationParams(page=1, size=10)
        items = list(range(5))
        page = Page.create(items=items, total=5, params=params)
        assert page.items == items
        assert page.total == 5
        assert page.page == 1
        assert page.size == 10
        assert page.pages == 1

    def test_create_multiple_pages(self) -> None:
        params = PaginationParams(page=2, size=10)
        items = list(range(10))
        page = Page.create(items=items, total=25, params=params)
        assert page.pages == 3

    def test_empty_result_has_one_page(self) -> None:
        params = PaginationParams()
        page = Page.create(items=[], total=0, params=params)
        assert page.pages == 1
        assert page.total == 0
