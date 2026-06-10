"""End-to-end tests for Profile API endpoints.

Covers:
- Happy path CRUD operations (create, read, list, update, delete)
- FK validation: invalid user_id returns 409
- Cascading deletes: profile deletion removes follows and channels
- Pagination
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_profile_fields,
    create_user,
    create_profile,
    create_channel,
    create_follow,
)


class TestProfileCreate:
    """Test profile creation endpoint (POST /api/v1/profiles)."""

    @pytest.mark.asyncio
    async def test_create_profile_success(self, client: AsyncClient) -> None:
        """Test successful profile creation."""
        user = await create_user(client)
        payload = TestDataGenerator.profile_data(user["id"])
        
        response = await client.post("/api/v1/profiles", json=payload)
        
        assert response.status_code == 201
        profile = response.json()
        assert_profile_fields(profile, user["id"], payload["display_name"])

    @pytest.mark.asyncio
    async def test_create_profile_invalid_user_fk(self, client: AsyncClient) -> None:
        """Test that invalid user_id returns 409 Conflict."""
        payload = TestDataGenerator.profile_data(user_id=999999)
        
        response = await client.post("/api/v1/profiles", json=payload)
        
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_profile_missing_user_id(self, client: AsyncClient) -> None:
        """Test that missing user_id returns 422."""
        payload = {"display_name": "Test Profile"}
        
        response = await client.post("/api/v1/profiles", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_profile_missing_display_name(self, client: AsyncClient) -> None:
        """Test that missing display_name returns 422."""
        user = await create_user(client)
        payload = {"user_id": user["id"]}
        
        response = await client.post("/api/v1/profiles", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_profile_with_optional_bio(self, client: AsyncClient) -> None:
        """Test creating profile with optional bio field."""
        user = await create_user(client)
        payload = TestDataGenerator.profile_data(
            user["id"],
            bio="This is my bio"
        )
        
        response = await client.post("/api/v1/profiles", json=payload)
        
        assert response.status_code == 201
        profile = response.json()
        assert profile["bio"] == "This is my bio"

    @pytest.mark.asyncio
    async def test_create_multiple_profiles_same_user(self, client: AsyncClient) -> None:
        """Test that same user can have multiple profiles."""
        user = await create_user(client)
        profile1 = await create_profile(client, user["id"])
        profile2 = await create_profile(client, user["id"])
        
        assert profile1["id"] != profile2["id"]
        assert profile1["user_id"] == user["id"]
        assert profile2["user_id"] == user["id"]


class TestProfileRead:
    """Test profile retrieval endpoint (GET /api/v1/profiles/{profile_id})."""

    @pytest.mark.asyncio
    async def test_get_profile_success(self, client: AsyncClient) -> None:
        """Test successful profile retrieval."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        response = await client.get(f"/api/v1/profiles/{profile['id']}")
        
        assert response.status_code == 200
        retrieved = response.json()
        assert_profile_fields(retrieved, user["id"], profile["display_name"])
        assert retrieved["id"] == profile["id"]

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, client: AsyncClient) -> None:
        """Test that non-existent profile returns 404."""
        response = await client.get("/api/v1/profiles/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_profile_invalid_id_type(self, client: AsyncClient) -> None:
        """Test that non-integer profile_id returns 422."""
        response = await client.get("/api/v1/profiles/invalid")
        assert response.status_code == 422


class TestProfileList:
    """Test profile listing endpoint (GET /api/v1/profiles)."""

    @pytest.mark.asyncio
    async def test_list_profiles_default_pagination(self, client: AsyncClient) -> None:
        """Test listing profiles with default pagination."""
        user1 = await create_user(client)
        user2 = await create_user(client)
        await create_profile(client, user1["id"])
        await create_profile(client, user2["id"])
        
        response = await client.get("/api/v1/profiles")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_profiles_custom_page_size(self, client: AsyncClient) -> None:
        """Test listing profiles with custom page size."""
        user = await create_user(client)
        for _ in range(5):
            await create_profile(client, user["id"])
        
        response = await client.get("/api/v1/profiles?page=1&size=3")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_profiles_pagination_boundaries(self, client: AsyncClient) -> None:
        """Test pagination boundaries."""
        user = await create_user(client)
        for _ in range(10):
            await create_profile(client, user["id"])
        
        # Valid: page=1&size=5
        response = await client.get("/api/v1/profiles?page=1&size=5")
        assert response.status_code == 200
        
        # Invalid: page=0
        response = await client.get("/api/v1/profiles?page=0&size=5")
        assert response.status_code == 422
        
        # Invalid: size=0
        response = await client.get("/api/v1/profiles?page=1&size=0")
        assert response.status_code == 422
        
        # Invalid: size>100
        response = await client.get("/api/v1/profiles?page=1&size=101")
        assert response.status_code == 422


class TestProfileUpdate:
    """Test profile update endpoint (PATCH /api/v1/profiles/{profile_id})."""

    @pytest.mark.asyncio
    async def test_patch_profile_display_name(self, client: AsyncClient) -> None:
        """Test updating profile display_name."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        new_name = f"Updated Profile {TestDataGenerator.next_id()}"
        
        response = await client.patch(
            f"/api/v1/profiles/{profile['id']}",
            json={"display_name": new_name}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["display_name"] == new_name
        assert updated["id"] == profile["id"]

    @pytest.mark.asyncio
    async def test_patch_profile_bio(self, client: AsyncClient) -> None:
        """Test updating profile bio."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        new_bio = "Updated bio text"
        
        response = await client.patch(
            f"/api/v1/profiles/{profile['id']}",
            json={"bio": new_bio}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["bio"] == new_bio

    @pytest.mark.asyncio
    async def test_patch_profile_multiple_fields(self, client: AsyncClient) -> None:
        """Test updating multiple profile fields."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        n = TestDataGenerator.next_id()
        
        response = await client.patch(
            f"/api/v1/profiles/{profile['id']}",
            json={
                "display_name": f"New Name {n}",
                "bio": f"New Bio {n}"
            }
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["display_name"] == f"New Name {n}"
        assert updated["bio"] == f"New Bio {n}"

    @pytest.mark.asyncio
    async def test_patch_profile_not_found(self, client: AsyncClient) -> None:
        """Test patching non-existent profile returns 404."""
        response = await client.patch(
            "/api/v1/profiles/999999",
            json={"display_name": "New Name"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_profile_preserves_user_id(self, client: AsyncClient) -> None:
        """Test that user_id cannot be changed through patch."""
        user1 = await create_user(client)
        user2 = await create_user(client)
        profile = await create_profile(client, user1["id"])
        
        # Try to change user_id (may be ignored or rejected)
        response = await client.patch(
            f"/api/v1/profiles/{profile['id']}",
            json={"user_id": user2["id"]}
        )
        
        # Verify it either succeeded but didn't change the FK, or rejected it
        if response.status_code == 200:
            updated = response.json()
            assert updated["user_id"] == user1["id"]


class TestProfileDelete:
    """Test profile deletion endpoint (DELETE /api/v1/profiles/{profile_id})."""

    @pytest.mark.asyncio
    async def test_delete_profile_success(self, client: AsyncClient) -> None:
        """Test successful profile deletion."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        response = await client.delete(f"/api/v1/profiles/{profile['id']}")
        
        assert response.status_code == 204
        
        # Verify profile is deleted
        get_response = await client.get(f"/api/v1/profiles/{profile['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent profile returns 404."""
        response = await client.delete("/api/v1/profiles/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile_cascades_follows(self, client: AsyncClient) -> None:
        """Test that deleting profile cascades to delete follows."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        
        # Delete the profile
        response = await client.delete(f"/api/v1/profiles/{profile['id']}")
        assert response.status_code == 204
        
        # Verify follow is also deleted (FK cascade)
        follow_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert follow_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile_cascades_channels(self, client: AsyncClient) -> None:
        """Test that deleting profile cascades to delete channels."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        channel = await create_channel(client, profile["id"])
        
        # Delete the profile
        response = await client.delete(f"/api/v1/profiles/{profile['id']}")
        assert response.status_code == 204
        
        # Verify channel is also deleted (FK cascade)
        channel_response = await client.get(f"/api/v1/channels/{channel['id']}")
        assert channel_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_profile_cascades_follows_and_channels(self, client: AsyncClient) -> None:
        """Test that deleting profile cascades to both follows and channels."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        # Create follow and channels
        follow = await create_follow(client, follower["id"], profile["id"])
        channel1 = await create_channel(client, profile["id"])
        channel2 = await create_channel(client, profile["id"])
        
        # Delete the profile
        response = await client.delete(f"/api/v1/profiles/{profile['id']}")
        assert response.status_code == 204
        
        # Verify all are deleted
        assert (await client.get(f"/api/v1/follows/{follow['id']}")).status_code == 404
        assert (await client.get(f"/api/v1/channels/{channel1['id']}")).status_code == 404
        assert (await client.get(f"/api/v1/channels/{channel2['id']}")).status_code == 404


class TestProfileWorkflows:
    """Test realistic multi-step profile workflows."""

    @pytest.mark.asyncio
    async def test_profile_setup_workflow(self, client: AsyncClient) -> None:
        """Test typical profile setup: create user -> create profile -> add channels."""
        # Create user
        user = await create_user(client)
        
        # Create profile
        profile = await create_profile(client, user["id"])
        
        # Add channels to profile
        channel1 = await create_channel(
            client,
            profile["id"],
            channel_name="YouTube"
        )
        channel2 = await create_channel(
            client,
            profile["id"],
            channel_name="Twitter"
        )
        
        # Verify all are linked
        get_profile = await client.get(f"/api/v1/profiles/{profile['id']}")
        assert get_profile.status_code == 200
        assert get_profile.json()["user_id"] == user["id"]
        
        get_ch1 = await client.get(f"/api/v1/channels/{channel1['id']}")
        assert get_ch1.status_code == 200
        assert get_ch1.json()["profile_id"] == profile["id"]

    @pytest.mark.asyncio
    async def test_profile_social_workflow(self, client: AsyncClient) -> None:
        """Test social workflow: create profiles, create follows."""
        # Create users
        user1 = await create_user(client)
        user2 = await create_user(client)
        user3 = await create_user(client)
        
        # Create profiles
        profile1 = await create_profile(client, user1["id"])
        profile2 = await create_profile(client, user2["id"])
        
        # Create follows
        follow1 = await create_follow(client, user1["id"], profile2["id"])
        follow2 = await create_follow(client, user3["id"], profile1["id"])
        
        # Verify follows exist
        assert (await client.get(f"/api/v1/follows/{follow1['id']}")).status_code == 200
        assert (await client.get(f"/api/v1/follows/{follow2['id']}")).status_code == 200
