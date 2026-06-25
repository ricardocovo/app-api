"""End-to-end tests for Profile endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_profile_fields,
    create_channel,
    create_follow,
    create_profile,
    create_user,
)


class TestProfileCreate:
    @pytest.mark.asyncio
    async def test_create_profile_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        payload = TestDataGenerator.profile_data(user["id"])
        response = await client.post("/api/v1/profiles", json=payload)
        assert response.status_code == 201
        assert_profile_fields(response.json(), user["id"], payload["name"])

    @pytest.mark.asyncio
    async def test_create_profile_invalid_user_fk(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.profile_data(str(uuid.uuid4()))
        response = await client.post("/api/v1/profiles", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_profile_missing_name(self, client: AsyncClient) -> None:
        user = await create_user(client)
        payload = {"user_id": user["id"]}
        response = await client.post("/api/v1/profiles", json=payload)
        assert response.status_code == 422


class TestProfileReadListUpdateDelete:
    @pytest.mark.asyncio
    async def test_read_profile_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        response = await client.get(f"/api/v1/profiles/{profile['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == profile["id"]

    @pytest.mark.asyncio
    async def test_read_profile_not_found(self, client: AsyncClient) -> None:
        response = await client.get(f"/api/v1/profiles/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_profiles_and_filter(self, client: AsyncClient) -> None:
        user = await create_user(client)
        p1 = await create_profile(client, user["id"])
        await create_profile(client, user["id"])
        response = await client.get(f"/api/v1/profiles?page=1&size=50&user_id={user['id']}")
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        returned_ids = {p["id"] for p in page["items"]}
        assert p1["id"] in returned_ids

    @pytest.mark.asyncio
    async def test_patch_profile(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        response = await client.patch(
            f"/api/v1/profiles/{profile['id']}",
            json={"name": "Renamed", "is_default": True, "is_public": False},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == "Renamed"
        assert updated["is_default"] is True
        assert updated["is_public"] is False

    @pytest.mark.asyncio
    async def test_delete_profile_cascade(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        channel = await create_channel(client, profile["id"])

        response = await client.delete(f"/api/v1/profiles/{profile['id']}")
        assert response.status_code == 204
        assert (await client.get(f"/api/v1/follows/{follow['id']}")).status_code == 404
        assert (await client.get(f"/api/v1/channels/{channel['id']}")).status_code == 404
