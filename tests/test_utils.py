"""Test utilities and helper functions for E2E tests."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient


class TestDataGenerator:
    """Generate unique test data to avoid conflicts."""

    _counter = 10000

    @classmethod
    def next_id(cls) -> int:
        cls._counter += 1
        return cls._counter

    @classmethod
    def user_data(cls, **overrides: Any) -> dict[str, str]:
        """Generate unique user data."""
        n = cls.next_id()
        data = {
            "username": f"test_user_{n}",
            "email": f"test_{n}@example.com",
            "password_hash": "hashed_password_123",
        }
        data.update(overrides)
        return data

    @classmethod
    def profile_data(cls, user_id: int, **overrides: Any) -> dict[str, Any]:
        """Generate unique profile data."""
        n = cls.next_id()
        data = {
            "user_id": user_id,
            "display_name": f"Profile {n}",
            "bio": f"Bio for test user {n}",
        }
        data.update(overrides)
        return data

    @classmethod
    def follow_data(cls, follower_id: int, profile_id: int) -> dict[str, int]:
        """Generate follow relationship data."""
        return {
            "follower_id": follower_id,
            "profile_id": profile_id,
        }

    @classmethod
    def channel_data(cls, profile_id: int, **overrides: Any) -> dict[str, Any]:
        """Generate unique channel data."""
        n = cls.next_id()
        data = {
            "profile_id": profile_id,
            "channel_name": f"Channel_{n}",
            "channel_url": f"https://example.com/channel_{n}",
        }
        data.update(overrides)
        return data


# ============================================================================
# Quick Creator Functions
# ============================================================================


async def create_user(
    client: AsyncClient,
    **overrides: Any,
) -> dict:
    """Create a user and return the full response."""
    payload = TestDataGenerator.user_data(**overrides)
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def create_profile(
    client: AsyncClient,
    user_id: int,
    **overrides: Any,
) -> dict:
    """Create a profile for the given user."""
    payload = TestDataGenerator.profile_data(user_id, **overrides)
    response = await client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 201, f"Failed to create profile: {response.text}"
    return response.json()


async def create_follow(
    client: AsyncClient,
    follower_id: int,
    profile_id: int,
) -> dict:
    """Create a follow relationship."""
    payload = TestDataGenerator.follow_data(follower_id, profile_id)
    response = await client.post("/api/v1/follows", json=payload)
    assert response.status_code == 201, f"Failed to create follow: {response.text}"
    return response.json()


async def create_channel(
    client: AsyncClient,
    profile_id: int,
    **overrides: Any,
) -> dict:
    """Create a channel for the given profile."""
    payload = TestDataGenerator.channel_data(profile_id, **overrides)
    response = await client.post("/api/v1/channels", json=payload)
    assert response.status_code == 201, f"Failed to create channel: {response.text}"
    return response.json()


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_user_fields(user: dict, expected_username: str, expected_email: str) -> None:
    """Assert that a user object has expected fields."""
    assert "id" in user
    assert "username" in user
    assert "email" in user
    assert "created_at" in user
    assert user["username"] == expected_username
    assert user["email"] == expected_email
    # password_hash should never be returned in responses
    assert "password_hash" not in user


def assert_profile_fields(profile: dict, expected_user_id: int, expected_name: str) -> None:
    """Assert that a profile object has expected fields."""
    assert "id" in profile
    assert "user_id" in profile
    assert "display_name" in profile
    assert "created_at" in profile
    assert "updated_at" in profile
    assert profile["user_id"] == expected_user_id
    assert profile["display_name"] == expected_name


def assert_follow_fields(follow: dict, expected_follower_id: int, expected_profile_id: int) -> None:
    """Assert that a follow object has expected fields."""
    assert "id" in follow
    assert "follower_id" in follow
    assert "profile_id" in follow
    assert "created_at" in follow
    assert follow["follower_id"] == expected_follower_id
    assert follow["profile_id"] == expected_profile_id


def assert_channel_fields(channel: dict, expected_profile_id: int, expected_name: str) -> None:
    """Assert that a channel object has expected fields."""
    assert "id" in channel
    assert "profile_id" in channel
    assert "channel_name" in channel
    assert "created_at" in channel
    assert "updated_at" in channel
    assert channel["profile_id"] == expected_profile_id
    assert channel["channel_name"] == expected_name


# ============================================================================
# Pagination Helpers
# ============================================================================


def assert_page_structure(page: dict, expected_items: int = None) -> None:
    """Assert that a response has valid page structure."""
    assert "items" in page
    assert "total" in page
    assert "page" in page
    assert "size" in page
    assert "pages" in page
    assert isinstance(page["items"], list)
    assert isinstance(page["total"], int)
    assert page["page"] >= 1
    assert page["size"] >= 1
    if expected_items is not None:
        assert len(page["items"]) == expected_items
