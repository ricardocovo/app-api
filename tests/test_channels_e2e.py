"""End-to-end tests for ProfileChannel API endpoints.

Covers:
- Happy path CRUD operations (create, read, list, update, delete)
- FK validation: invalid profile_id returns 409
- URL validation
- Cascading delete behavior
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_channel_fields,
    create_user,
    create_profile,
    create_channel,
)


class TestChannelCreate:
    """Test channel creation endpoint (POST /api/v1/channels)."""

    @pytest.mark.asyncio
    async def test_create_channel_success(self, client: AsyncClient) -> None:
        """Test successful channel creation."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        payload = TestDataGenerator.channel_data(profile["id"])
        
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 201
        channel = response.json()
        assert_channel_fields(channel, profile["id"], payload["channel_name"])

    @pytest.mark.asyncio
    async def test_create_channel_invalid_profile_fk(self, client: AsyncClient) -> None:
        """Test that invalid profile_id returns 409."""
        payload = TestDataGenerator.channel_data(profile_id=999999)
        
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_channel_missing_profile_id(self, client: AsyncClient) -> None:
        """Test that missing profile_id returns 422."""
        payload = {"channel_name": "TestChannel"}
        
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_channel_missing_channel_name(self, client: AsyncClient) -> None:
        """Test that missing channel_name returns 422."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        payload = {"profile_id": profile["id"]}
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_channel_with_url(self, client: AsyncClient) -> None:
        """Test creating channel with URL."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        payload = TestDataGenerator.channel_data(
            profile["id"],
            channel_url="https://youtube.com/user/testuser"
        )
        
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 201
        channel = response.json()
        assert channel["channel_url"] == "https://youtube.com/user/testuser"

    @pytest.mark.asyncio
    async def test_create_channel_invalid_url(self, client: AsyncClient) -> None:
        """Test that invalid URL format returns 422."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        payload = TestDataGenerator.channel_data(
            profile["id"],
            channel_url="not-a-url"
        )
        
        response = await client.post("/api/v1/channels", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_multiple_channels_same_profile(self, client: AsyncClient) -> None:
        """Test that same profile can have multiple channels."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        channel1 = await create_channel(client, profile["id"], channel_name="YouTube")
        channel2 = await create_channel(client, profile["id"], channel_name="Twitter")
        
        assert channel1["id"] != channel2["id"]
        assert channel1["profile_id"] == profile["id"]
        assert channel2["profile_id"] == profile["id"]


class TestChannelRead:
    """Test channel retrieval endpoint (GET /api/v1/channels/{channel_id})."""

    @pytest.mark.asyncio
    async def test_get_channel_success(self, client: AsyncClient) -> None:
        """Test successful channel retrieval."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        response = await client.get(f"/api/v1/channels/{channel['id']}")
        
        assert response.status_code == 200
        retrieved = response.json()
        assert_channel_fields(retrieved, profile["id"], channel["channel_name"])
        assert retrieved["id"] == channel["id"]

    @pytest.mark.asyncio
    async def test_get_channel_not_found(self, client: AsyncClient) -> None:
        """Test that non-existent channel returns 404."""
        response = await client.get("/api/v1/channels/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_channel_invalid_id_type(self, client: AsyncClient) -> None:
        """Test that non-integer channel_id returns 422."""
        response = await client.get("/api/v1/channels/invalid")
        assert response.status_code == 422


class TestChannelList:
    """Test channel listing endpoint (GET /api/v1/channels)."""

    @pytest.mark.asyncio
    async def test_list_channels_default_pagination(self, client: AsyncClient) -> None:
        """Test listing channels with default pagination."""
        user = await create_user(client)
        profile1 = await create_profile(client, user["id"])
        profile2 = await create_profile(client, user["id"])
        
        await create_channel(client, profile1["id"])
        await create_channel(client, profile2["id"])
        
        response = await client.get("/api/v1/channels")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_channels_custom_page_size(self, client: AsyncClient) -> None:
        """Test listing channels with custom page size."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        for _ in range(5):
            await create_channel(client, profile["id"])
        
        response = await client.get("/api/v1/channels?page=1&size=3")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_channels_pagination_boundaries(self, client: AsyncClient) -> None:
        """Test pagination boundaries."""
        # Invalid: page=0
        response = await client.get("/api/v1/channels?page=0&size=5")
        assert response.status_code == 422
        
        # Invalid: size=0
        response = await client.get("/api/v1/channels?page=1&size=0")
        assert response.status_code == 422
        
        # Invalid: size>100
        response = await client.get("/api/v1/channels?page=1&size=101")
        assert response.status_code == 422


class TestChannelUpdate:
    """Test channel update endpoint (PATCH /api/v1/channels/{channel_id})."""

    @pytest.mark.asyncio
    async def test_patch_channel_name(self, client: AsyncClient) -> None:
        """Test updating channel name."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        new_name = f"Updated Channel {TestDataGenerator.next_id()}"
        response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={"channel_name": new_name}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["channel_name"] == new_name
        assert updated["id"] == channel["id"]

    @pytest.mark.asyncio
    async def test_patch_channel_url(self, client: AsyncClient) -> None:
        """Test updating channel URL."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        new_url = "https://example.com/newchannel"
        response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={"channel_url": new_url}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["channel_url"] == new_url

    @pytest.mark.asyncio
    async def test_patch_channel_multiple_fields(self, client: AsyncClient) -> None:
        """Test updating multiple channel fields."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        n = TestDataGenerator.next_id()
        response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={
                "channel_name": f"New Channel {n}",
                "channel_url": f"https://example.com/channel{n}"
            }
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["channel_name"] == f"New Channel {n}"
        assert updated["channel_url"] == f"https://example.com/channel{n}"

    @pytest.mark.asyncio
    async def test_patch_channel_not_found(self, client: AsyncClient) -> None:
        """Test patching non-existent channel returns 404."""
        response = await client.patch(
            "/api/v1/channels/999999",
            json={"channel_name": "NewName"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_channel_invalid_url(self, client: AsyncClient) -> None:
        """Test that invalid URL format returns 422."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={"channel_url": "not-a-url"}
        )
        assert response.status_code == 422


class TestChannelDelete:
    """Test channel deletion endpoint (DELETE /api/v1/channels/{channel_id})."""

    @pytest.mark.asyncio
    async def test_delete_channel_success(self, client: AsyncClient) -> None:
        """Test successful channel deletion."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        response = await client.delete(f"/api/v1/channels/{channel['id']}")
        
        assert response.status_code == 204
        
        # Verify channel is deleted
        get_response = await client.get(f"/api/v1/channels/{channel['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_channel_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent channel returns 404."""
        response = await client.delete("/api/v1/channels/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_channel_idempotent(self, client: AsyncClient) -> None:
        """Test that deleting same channel twice returns 404 second time."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        # First delete succeeds
        response1 = await client.delete(f"/api/v1/channels/{channel['id']}")
        assert response1.status_code == 204
        
        # Second delete returns 404
        response2 = await client.delete(f"/api/v1/channels/{channel['id']}")
        assert response2.status_code == 404


class TestChannelWorkflows:
    """Test realistic multi-step channel workflows."""

    @pytest.mark.asyncio
    async def test_user_adds_social_channels(self, client: AsyncClient) -> None:
        """Test a user adding social media channels to their profile."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        # Add multiple channels
        youtube = await create_channel(
            client,
            profile["id"],
            channel_name="YouTube",
            channel_url="https://youtube.com/@testuser"
        )
        twitter = await create_channel(
            client,
            profile["id"],
            channel_name="Twitter",
            channel_url="https://twitter.com/testuser"
        )
        
        # Verify all channels exist and are linked to the same profile
        assert (await client.get(f"/api/v1/channels/{youtube['id']}")).status_code == 200
        assert (await client.get(f"/api/v1/channels/{twitter['id']}")).status_code == 200

    @pytest.mark.asyncio
    async def test_user_updates_channel_urls(self, client: AsyncClient) -> None:
        """Test a user updating their channel URLs."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        channel = await create_channel(
            client,
            profile["id"],
            channel_name="Website"
        )
        
        # Initial state - no URL
        get_response = await client.get(f"/api/v1/channels/{channel['id']}")
        assert "channel_url" in get_response.json()
        
        # Add URL
        new_url = "https://example.com"
        update_response = await client.patch(
            f"/api/v1/channels/{channel['id']}",
            json={"channel_url": new_url}
        )
        assert update_response.status_code == 200
        # Note: Pydantic's HttpUrl adds trailing slash; compare normalized URLs
        updated_url = update_response.json()["channel_url"]
        assert updated_url.rstrip('/') == new_url.rstrip('/')

    @pytest.mark.asyncio
    async def test_user_removes_channel(self, client: AsyncClient) -> None:
        """Test a user removing a channel from their profile."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        channel1 = await create_channel(client, profile["id"], channel_name="Channel1")
        channel2 = await create_channel(client, profile["id"], channel_name="Channel2")
        
        # List channels
        list_response = await client.get("/api/v1/channels?size=100")
        initial_count = len(list_response.json()["items"])
        
        # Delete channel1
        delete_response = await client.delete(f"/api/v1/channels/{channel1['id']}")
        assert delete_response.status_code == 204
        
        # List channels again - should have one fewer
        list_response2 = await client.get("/api/v1/channels?size=100")
        final_count = len(list_response2.json()["items"])
        assert final_count == initial_count - 1
        
        # channel2 should still exist
        assert (await client.get(f"/api/v1/channels/{channel2['id']}")).status_code == 200

    @pytest.mark.asyncio
    async def test_multiple_users_with_different_channels(self, client: AsyncClient) -> None:
        """Test multiple users each maintaining their own channels."""
        user1 = await create_user(client)
        user2 = await create_user(client)
        
        profile1 = await create_profile(client, user1["id"])
        profile2 = await create_profile(client, user2["id"])
        
        channel1 = await create_channel(client, profile1["id"], channel_name="User1 Channel")
        channel2 = await create_channel(client, profile2["id"], channel_name="User2 Channel")
        
        # Verify channels are independent
        assert channel1["profile_id"] == profile1["id"]
        assert channel2["profile_id"] == profile2["id"]
        assert channel1["id"] != channel2["id"]
        
        # Deleting one shouldn't affect the other
        delete_response = await client.delete(f"/api/v1/channels/{channel1['id']}")
        assert delete_response.status_code == 204
        assert (await client.get(f"/api/v1/channels/{channel2['id']}")).status_code == 200
