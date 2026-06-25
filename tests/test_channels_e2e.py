"""End-to-end tests for Channel endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_channel_fields,
    assert_page_structure,
    create_channel,
    create_profile,
    create_user,
)


class TestChannelCreateReadListUpdateDelete:
    @pytest.mark.asyncio
    async def test_create_channel_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        payload = TestDataGenerator.channel_data(profile["id"])
        response = await client.post("/api/v1/channels", json=payload)
        assert response.status_code == 201
        assert_channel_fields(response.json(), profile["id"], payload["channel_title"])

    @pytest.mark.asyncio
    async def test_create_channel_invalid_profile_fk(self, client: AsyncClient) -> None:
        payload = TestDataGenerator.channel_data(str(uuid.uuid4()))
        response = await client.post("/api/v1/channels", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_channel_missing_required_field(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        response = await client.post(
            "/api/v1/channels",
            json={"profile_id": profile["id"], "youtube_channel_id": "yt_missing_title"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_channel_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        response = await client.get(f"/api/v1/channels/{channel['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == channel["id"]

    @pytest.mark.asyncio
    async def test_get_channel_not_found(self, client: AsyncClient) -> None:
        response = await client.get(f"/api/v1/channels/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_channel_invalid_id(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/channels/invalid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_channels_with_profile_filter(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        ch = await create_channel(client, profile["id"])
        response = await client.get(
            f"/api/v1/channels?page=1&size=50&profile_id={profile['id']}"
        )
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert [item["id"] for item in page["items"]] == [ch["id"]]

    @pytest.mark.asyncio
    async def test_patch_channel(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={"channel_title": "Updated Title", "thumbnail_url": "https://example.com/new-thumb.png"},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["channel_title"] == "Updated Title"
        assert updated["thumbnail_url"] == "https://example.com/new-thumb.png"

    @pytest.mark.asyncio
    async def test_delete_channel_success(self, client: AsyncClient) -> None:
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        response = await client.delete(f"/api/v1/channels/{channel['id']}")
        assert response.status_code == 204
        assert (await client.get(f"/api/v1/channels/{channel['id']}")).status_code == 404
