"""End-to-end tests for Follow endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    assert_follow_fields,
    assert_page_structure,
    create_follow,
    create_profile,
    create_user,
)


class TestFollowCreateReadListDelete:
    @pytest.mark.asyncio
    async def test_create_follow_success(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])

        response = await client.post(
            "/api/v1/follows",
            json={"follower_id": follower["id"], "profile_id": profile["id"]},
        )
        assert response.status_code == 201
        assert_follow_fields(response.json(), follower["id"], profile["id"])

    @pytest.mark.asyncio
    async def test_create_follow_duplicate_conflict(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        payload = {"follower_id": follower["id"], "profile_id": profile["id"]}
        await client.post("/api/v1/follows", json=payload)
        response = await client.post("/api/v1/follows", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_follow_invalid_fk_conflict(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/follows",
            json={"follower_id": str(uuid.uuid4()), "profile_id": str(uuid.uuid4())},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_read_follow_success(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == follow["id"]

    @pytest.mark.asyncio
    async def test_list_follows_with_filters(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])

        response = await client.get(
            f"/api/v1/follows?page=1&size=50&follower_id={follower['id']}&profile_id={profile['id']}"
        )
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert [item["id"] for item in page["items"]] == [follow["id"]]

    @pytest.mark.asyncio
    async def test_delete_follow_success_and_refollow(self, client: AsyncClient) -> None:
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])

        response = await client.delete(f"/api/v1/follows/{follow['id']}")
        assert response.status_code == 204
        assert (await client.get(f"/api/v1/follows/{follow['id']}")).status_code == 404

        response2 = await client.post(
            "/api/v1/follows",
            json={"follower_id": follower["id"], "profile_id": profile["id"]},
        )
        assert response2.status_code == 201
