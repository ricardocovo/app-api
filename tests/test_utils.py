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
    def user_data(cls, **overrides: Any) -> dict[str, Any]:
        n = cls.next_id()
        data: dict[str, Any] = {
            "email": f"test_{n}@example.com",
            "name": f"Test User {n}",
            "google_id": f"google_{n}",
        }
        data.update(overrides)
        return data

    @classmethod
    def profile_data(cls, user_id: str, **overrides: Any) -> dict[str, Any]:
        n = cls.next_id()
        data: dict[str, Any] = {
            "user_id": user_id,
            "name": f"Profile {n}",
            "is_default": False,
            "is_public": True,
        }
        data.update(overrides)
        return data

    @classmethod
    def follow_data(cls, follower_id: str, profile_id: str) -> dict[str, str]:
        return {"follower_id": follower_id, "profile_id": profile_id}

    @classmethod
    def channel_data(cls, profile_id: str, **overrides: Any) -> dict[str, Any]:
        n = cls.next_id()
        data: dict[str, Any] = {
            "profile_id": profile_id,
            "youtube_channel_id": f"yt_{n}",
            "channel_title": f"Channel {n}",
            "thumbnail_url": f"https://example.com/thumb-{n}.png",
        }
        data.update(overrides)
        return data


async def create_user(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    payload = TestDataGenerator.user_data(**overrides)
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def create_profile(
    client: AsyncClient, user_id: str, **overrides: Any
) -> dict[str, Any]:
    payload = TestDataGenerator.profile_data(user_id, **overrides)
    response = await client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 201, f"Failed to create profile: {response.text}"
    return response.json()


async def create_follow(
    client: AsyncClient, follower_id: str, profile_id: str
) -> dict[str, Any]:
    payload = TestDataGenerator.follow_data(follower_id, profile_id)
    response = await client.post("/api/v1/follows", json=payload)
    assert response.status_code == 201, f"Failed to create follow: {response.text}"
    return response.json()


async def create_channel(
    client: AsyncClient, profile_id: str, **overrides: Any
) -> dict[str, Any]:
    payload = TestDataGenerator.channel_data(profile_id, **overrides)
    response = await client.post("/api/v1/channels", json=payload)
    assert response.status_code == 201, f"Failed to create channel: {response.text}"
    return response.json()


def assert_user_fields(user: dict[str, Any], expected_name: str, expected_email: str) -> None:
    assert "id" in user
    assert "email" in user
    assert "name" in user
    assert "created_at" in user
    assert "updated_at" in user
    assert user["name"] == expected_name
    assert user["email"] == expected_email


def assert_profile_fields(
    profile: dict[str, Any], expected_user_id: str, expected_name: str
) -> None:
    assert "id" in profile
    assert "user_id" in profile
    assert "name" in profile
    assert "is_default" in profile
    assert "is_public" in profile
    assert profile["user_id"] == expected_user_id
    assert profile["name"] == expected_name


def assert_follow_fields(
    follow: dict[str, Any], expected_follower_id: str, expected_profile_id: str
) -> None:
    assert "id" in follow
    assert "follower_id" in follow
    assert "profile_id" in follow
    assert "created_at" in follow
    assert follow["follower_id"] == expected_follower_id
    assert follow["profile_id"] == expected_profile_id


def assert_channel_fields(
    channel: dict[str, Any], expected_profile_id: str, expected_title: str
) -> None:
    assert "id" in channel
    assert "profile_id" in channel
    assert "youtube_channel_id" in channel
    assert "channel_title" in channel
    assert channel["profile_id"] == expected_profile_id
    assert channel["channel_title"] == expected_title


def assert_page_structure(page: dict[str, Any], expected_items: int | None = None) -> None:
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
