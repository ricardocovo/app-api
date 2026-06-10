"""End-to-end tests for ProfileFollow API endpoints.

Covers:
- Happy path CRUD operations (create, read, list, delete)
- Error cases: duplicate follows (409), invalid follower/profile ID (409), not found
- Multi-user follow scenarios
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_follow_fields,
    create_user,
    create_profile,
    create_follow,
)


class TestFollowCreate:
    """Test follow creation endpoint (POST /api/v1/follows)."""

    @pytest.mark.asyncio
    async def test_create_follow_success(self, client: AsyncClient) -> None:
        """Test successful follow creation."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        payload = TestDataGenerator.follow_data(follower["id"], profile["id"])
        response = await client.post("/api/v1/follows", json=payload)
        
        assert response.status_code == 201
        follow = response.json()
        assert_follow_fields(follow, follower["id"], profile["id"])

    @pytest.mark.asyncio
    async def test_create_follow_duplicate_409(self, client: AsyncClient) -> None:
        """Test that duplicate follow returns 409 Conflict."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        payload = TestDataGenerator.follow_data(follower["id"], profile["id"])
        await client.post("/api/v1/follows", json=payload)
        
        # Try to create again
        response = await client.post("/api/v1/follows", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_follow_invalid_follower_fk(self, client: AsyncClient) -> None:
        """Test that invalid follower_id returns 409."""
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        payload = TestDataGenerator.follow_data(999999, profile["id"])
        response = await client.post("/api/v1/follows", json=payload)
        
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_follow_invalid_profile_fk(self, client: AsyncClient) -> None:
        """Test that invalid profile_id returns 409."""
        follower = await create_user(client)
        
        payload = TestDataGenerator.follow_data(follower["id"], 999999)
        response = await client.post("/api/v1/follows", json=payload)
        
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_follow_missing_follower_id(self, client: AsyncClient) -> None:
        """Test that missing follower_id returns 422."""
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        payload = {"profile_id": profile["id"]}
        response = await client.post("/api/v1/follows", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_follow_missing_profile_id(self, client: AsyncClient) -> None:
        """Test that missing profile_id returns 422."""
        follower = await create_user(client)
        
        payload = {"follower_id": follower["id"]}
        response = await client.post("/api/v1/follows", json=payload)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_self_follow(self, client: AsyncClient) -> None:
        """Test that same user can follow their own profile (if allowed by design)."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        payload = TestDataGenerator.follow_data(user["id"], profile["id"])
        response = await client.post("/api/v1/follows", json=payload)
        
        # Design allows this - user can follow their own profile
        assert response.status_code == 201


class TestFollowRead:
    """Test follow retrieval endpoint (GET /api/v1/follows/{follow_id})."""

    @pytest.mark.asyncio
    async def test_get_follow_success(self, client: AsyncClient) -> None:
        """Test successful follow retrieval."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        
        response = await client.get(f"/api/v1/follows/{follow['id']}")
        
        assert response.status_code == 200
        retrieved = response.json()
        assert_follow_fields(retrieved, follower["id"], profile["id"])

    @pytest.mark.asyncio
    async def test_get_follow_not_found(self, client: AsyncClient) -> None:
        """Test that non-existent follow returns 404."""
        response = await client.get("/api/v1/follows/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_follow_invalid_id_type(self, client: AsyncClient) -> None:
        """Test that non-integer follow_id returns 422."""
        response = await client.get("/api/v1/follows/invalid")
        assert response.status_code == 422


class TestFollowList:
    """Test follow listing endpoint (GET /api/v1/follows)."""

    @pytest.mark.asyncio
    async def test_list_follows_default_pagination(self, client: AsyncClient) -> None:
        """Test listing follows with default pagination."""
        follower1 = await create_user(client)
        follower2 = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        await create_follow(client, follower1["id"], profile["id"])
        await create_follow(client, follower2["id"], profile["id"])
        
        response = await client.get("/api/v1/follows")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_follows_custom_page_size(self, client: AsyncClient) -> None:
        """Test listing follows with custom page size."""
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        for _ in range(5):
            follower = await create_user(client)
            await create_follow(client, follower["id"], profile["id"])
        
        response = await client.get("/api/v1/follows?page=1&size=3")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_follows_pagination_boundaries(self, client: AsyncClient) -> None:
        """Test pagination boundaries."""
        # Invalid: page=0
        response = await client.get("/api/v1/follows?page=0&size=5")
        assert response.status_code == 422
        
        # Invalid: size=0
        response = await client.get("/api/v1/follows?page=1&size=0")
        assert response.status_code == 422
        
        # Invalid: size>100
        response = await client.get("/api/v1/follows?page=1&size=101")
        assert response.status_code == 422


class TestFollowDelete:
    """Test follow deletion endpoint (DELETE /api/v1/follows/{follow_id})."""

    @pytest.mark.asyncio
    async def test_delete_follow_success(self, client: AsyncClient) -> None:
        """Test successful follow deletion."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        
        response = await client.delete(f"/api/v1/follows/{follow['id']}")
        
        assert response.status_code == 204
        
        # Verify follow is deleted
        get_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_follow_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent follow returns 404."""
        response = await client.delete("/api/v1/follows/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_follow_idempotent_second_delete_404(self, client: AsyncClient) -> None:
        """Test that deleting same follow twice returns 404 second time."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        
        # First delete succeeds
        response1 = await client.delete(f"/api/v1/follows/{follow['id']}")
        assert response1.status_code == 204
        
        # Second delete returns 404
        response2 = await client.delete(f"/api/v1/follows/{follow['id']}")
        assert response2.status_code == 404


class TestFollowWorkflows:
    """Test realistic multi-step follow workflows."""

    @pytest.mark.asyncio
    async def test_fan_follows_creator(self, client: AsyncClient) -> None:
        """Test a fan following a creator workflow."""
        # Creator creates account and profile
        creator = await create_user(client)
        creator_profile = await create_profile(client, creator["id"])
        
        # Fan creates account
        fan = await create_user(client)
        
        # Fan follows creator's profile
        follow = await create_follow(client, fan["id"], creator_profile["id"])
        
        # Verify follow exists
        get_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["follower_id"] == fan["id"]

    @pytest.mark.asyncio
    async def test_multiple_users_follow_same_profile(self, client: AsyncClient) -> None:
        """Test multiple users following the same profile."""
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        followers = [await create_user(client) for _ in range(3)]
        follows = [await create_follow(client, f["id"], profile["id"]) for f in followers]
        
        # Verify all follows exist and are different
        follow_ids = [f["id"] for f in follows]
        assert len(set(follow_ids)) == 3
        
        # List all follows and verify all are present
        list_response = await client.get("/api/v1/follows?size=100")
        all_follow_ids = [f["id"] for f in list_response.json()["items"]]
        for fid in follow_ids:
            assert fid in all_follow_ids

    @pytest.mark.asyncio
    async def test_user_follows_multiple_profiles(self, client: AsyncClient) -> None:
        """Test a user following multiple profiles."""
        follower = await create_user(client)
        
        # Create multiple creators with their profiles
        creators = [await create_user(client) for _ in range(3)]
        profiles = [await create_profile(client, c["id"]) for c in creators]
        
        # Follower follows all profiles
        follows = [await create_follow(client, follower["id"], p["id"]) for p in profiles]
        
        # Verify all follows were created
        follow_ids = [f["id"] for f in follows]
        assert len(set(follow_ids)) == 3
        
        # Verify each follow individually
        for follow in follows:
            get_response = await client.get(f"/api/v1/follows/{follow['id']}")
            assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_follow_then_unfollow(self, client: AsyncClient) -> None:
        """Test following and then unfollowing workflow."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        
        # Follow
        follow = await create_follow(client, follower["id"], profile["id"])
        get_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert get_response.status_code == 200
        
        # Unfollow
        delete_response = await client.delete(f"/api/v1/follows/{follow['id']}")
        assert delete_response.status_code == 204
        
        # Verify follow is gone
        get_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert get_response.status_code == 404
        
        # Can follow again (even if ID is reused by SQLite)
        follow2 = await create_follow(client, follower["id"], profile["id"])
        assert follow2["follower_id"] == follower["id"]
        assert follow2["profile_id"] == profile["id"]
