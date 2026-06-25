"""End-to-end tests for User endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_user_fields,
    create_channel,
    create_follow,
    create_profile,
    create_user,
)


class TestUserCreate:
    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.user_data()
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 201
        assert_user_fields(response.json(), payload["name"], payload["email"])

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_conflict(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.user_data()
        await client.post("/api/v1/users", json=payload)
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_missing_email(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.user_data()
        del payload["email"]
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.user_data(email="not-an-email")
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422


class TestUserReadAndList:
    @pytest.mark.asyncio
    async def test_get_user_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        response = await client.get(f"/api/v1/users/{user['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == user["id"]

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient) -> None:
        response = await client.get(f"/api/v1/users/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_invalid_id(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/invalid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_with_filter(self, client: AsyncClient) -> None:
        email = f"filter_{TestDataGenerator.next_id()}@example.com"
        created = await create_user(client, email=email)
        await create_user(client)
        response = await client.get(f"/api/v1/users?page=1&size=50&email={email}")
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert [u["id"] for u in page["items"]] == [created["id"]]


class TestUserUpdateDeleteAndCascade:
    @pytest.mark.asyncio
    async def test_patch_user(self, client: AsyncClient) -> None:
        user = await create_user(client)
        new_name = f"Updated {TestDataGenerator.next_id()}"
        response = await client.patch(f"/api/v1/users/{user['id']}", json={"name": new_name})
        assert response.status_code == 200
        assert response.json()["name"] == new_name

    @pytest.mark.asyncio
    async def test_patch_user_not_found(self, client: AsyncClient) -> None:
        response = await client.patch(f"/api/v1/users/{uuid.uuid4()}", json={"name": "x"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        response = await client.delete(f"/api/v1/users/{user['id']}")
        assert response.status_code == 204
        assert (await client.get(f"/api/v1/users/{user['id']}")).status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_cascades_profile_follow_channel(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        channel = await create_channel(client, profile["id"])

        response = await client.delete(f"/api/v1/users/{owner['id']}")
        assert response.status_code == 204
        assert (await client.get(f"/api/v1/profiles/{profile['id']}")).status_code == 404
        assert (await client.get(f"/api/v1/follows/{follow['id']}")).status_code == 404
        assert (await client.get(f"/api/v1/channels/{channel['id']}")).status_code == 404
