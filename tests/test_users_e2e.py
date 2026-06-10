"""End-to-end tests for User API endpoints.

Covers:
- Happy path CRUD operations (create, read, list, update, delete)
- Error cases: duplicate username, missing fields, invalid email, not found, conflict
- Pagination: valid/invalid page sizes, boundary conditions
- Cascading deletes: user deletion removes profiles, follows, channels
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.test_utils import (
    TestDataGenerator,
    assert_page_structure,
    assert_user_fields,
    create_user,
    create_profile,
    create_follow,
)


class TestUserCreate:
    """Test user creation endpoint (POST /api/v1/users)."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, client: AsyncClient) -> None:
        """Test successful user creation."""
        payload = TestDataGenerator.user_data()
        response = await client.post("/api/v1/users", json=payload)
        
        assert response.status_code == 201
        user = response.json()
        assert_user_fields(user, payload["username"], payload["email"])

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username_conflict(self, client: AsyncClient) -> None:
        """Test that duplicate username returns 409 Conflict."""
        payload = TestDataGenerator.user_data()
        await client.post("/api/v1/users", json=payload)
        
        # Try to create again with same username
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_conflict(self, client: AsyncClient) -> None:
        """Test that duplicate email returns 409 Conflict."""
        n1 = TestDataGenerator.next_id()
        n2 = TestDataGenerator.next_id()
        
        payload1 = {
            "username": f"user_{n1}",
            "email": "shared@example.com",
            "password_hash": "hash1"
        }
        await client.post("/api/v1/users", json=payload1)
        
        payload2 = {
            "username": f"user_{n2}",
            "email": "shared@example.com",
            "password_hash": "hash2"
        }
        response = await client.post("/api/v1/users", json=payload2)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_user_missing_username(self, client: AsyncClient) -> None:
        """Test that missing username returns 422 Unprocessable Entity."""
        payload = TestDataGenerator.user_data()
        del payload["username"]
        
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_missing_email(self, client: AsyncClient) -> None:
        """Test that missing email returns 422."""
        payload = TestDataGenerator.user_data()
        del payload["email"]
        
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_missing_password(self, client: AsyncClient) -> None:
        """Test that missing password_hash returns 422."""
        payload = TestDataGenerator.user_data()
        del payload["password_hash"]
        
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_invalid_email_format(self, client: AsyncClient) -> None:
        """Test that invalid email format returns 422."""
        payload = TestDataGenerator.user_data(email="not-an-email")
        response = await client.post("/api/v1/users", json=payload)
        assert response.status_code == 422


class TestUserRead:
    """Test user retrieval endpoint (GET /api/v1/users/{user_id})."""

    @pytest.mark.asyncio
    async def test_get_user_success(self, client: AsyncClient) -> None:
        """Test successful user retrieval."""
        created = await create_user(client)
        
        response = await client.get(f"/api/v1/users/{created['id']}")
        
        assert response.status_code == 200
        user = response.json()
        assert_user_fields(user, created["username"], created["email"])
        assert user["id"] == created["id"]

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client: AsyncClient) -> None:
        """Test that non-existent user returns 404."""
        response = await client.get("/api/v1/users/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_invalid_id_type(self, client: AsyncClient) -> None:
        """Test that non-integer user_id returns 422."""
        response = await client.get("/api/v1/users/invalid")
        assert response.status_code == 422


class TestUserList:
    """Test user listing endpoint (GET /api/v1/users)."""

    @pytest.mark.asyncio
    async def test_list_users_default_pagination(self, client: AsyncClient) -> None:
        """Test listing users with default pagination."""
        await create_user(client)
        await create_user(client)
        
        response = await client.get("/api/v1/users")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_users_custom_page_size(self, client: AsyncClient) -> None:
        """Test listing users with custom page size."""
        for _ in range(5):
            await create_user(client)
        
        response = await client.get("/api/v1/users?page=1&size=3")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        assert len(page["items"]) == 3
        assert page["size"] == 3

    @pytest.mark.asyncio
    async def test_list_users_pagination_page_2(self, client: AsyncClient) -> None:
        """Test pagination works across pages."""
        for _ in range(10):
            await create_user(client)
        
        page1 = await client.get("/api/v1/users?page=1&size=5")
        page2 = await client.get("/api/v1/users?page=2&size=5")
        
        assert page1.status_code == 200
        assert page2.status_code == 200
        
        page1_data = page1.json()
        page2_data = page2.json()
        
        # Different users on different pages
        page1_ids = [u["id"] for u in page1_data["items"]]
        page2_ids = [u["id"] for u in page2_data["items"]]
        assert len(set(page1_ids) & set(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_list_users_invalid_page(self, client: AsyncClient) -> None:
        """Test that page < 1 returns 422."""
        response = await client.get("/api/v1/users?page=0&size=10")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_invalid_size_zero(self, client: AsyncClient) -> None:
        """Test that size < 1 returns 422."""
        response = await client.get("/api/v1/users?page=1&size=0")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_size_exceeds_max(self, client: AsyncClient) -> None:
        """Test that size > 100 returns 422."""
        response = await client.get("/api/v1/users?page=1&size=101")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_users_with_email_filter(self, client: AsyncClient) -> None:
        """Test listing users with email filter."""
        email1 = f"alice_{TestDataGenerator.next_id()}@example.com"
        email2 = f"bob_{TestDataGenerator.next_id()}@example.com"
        
        user1 = await create_user(client, email=email1)
        await create_user(client, email=email2)
        
        # Filter by exact email
        response = await client.get(f"/api/v1/users?email={email1}")
        
        assert response.status_code == 200
        page = response.json()
        assert_page_structure(page)
        # Should find the user with exact email
        found_ids = [u["id"] for u in page["items"]]
        assert user1["id"] in found_ids


class TestUserUpdate:
    """Test user update endpoint (PATCH /api/v1/users/{user_id})."""

    @pytest.mark.asyncio
    async def test_patch_user_username(self, client: AsyncClient) -> None:
        """Test updating user username."""
        user = await create_user(client)
        new_username = f"updated_{TestDataGenerator.next_id()}"
        
        response = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={"username": new_username}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["username"] == new_username
        assert updated["id"] == user["id"]

    @pytest.mark.asyncio
    async def test_patch_user_email(self, client: AsyncClient) -> None:
        """Test updating user email."""
        user = await create_user(client)
        new_email = f"new_{TestDataGenerator.next_id()}@example.com"
        
        response = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={"email": new_email}
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["email"] == new_email

    @pytest.mark.asyncio
    async def test_patch_user_multiple_fields(self, client: AsyncClient) -> None:
        """Test updating multiple fields at once."""
        user = await create_user(client)
        n = TestDataGenerator.next_id()
        
        response = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={
                "username": f"updated_{n}",
                "email": f"updated_{n}@example.com"
            }
        )
        
        assert response.status_code == 200
        updated = response.json()
        assert updated["username"] == f"updated_{n}"
        assert updated["email"] == f"updated_{n}@example.com"

    @pytest.mark.asyncio
    async def test_patch_user_not_found(self, client: AsyncClient) -> None:
        """Test patching non-existent user returns 404."""
        response = await client.patch(
            "/api/v1/users/999999",
            json={"username": "newname"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_patch_user_duplicate_username_conflict(self, client: AsyncClient) -> None:
        """Test that patching to duplicate username returns 409."""
        user1 = await create_user(client)
        user2 = await create_user(client)
        
        # Try to give user2 the same username as user1
        response = await client.patch(
            f"/api/v1/users/{user2['id']}",
            json={"username": user1["username"]}
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_patch_user_invalid_email_format(self, client: AsyncClient) -> None:
        """Test that invalid email format returns 422."""
        user = await create_user(client)
        
        response = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={"email": "not-an-email"}
        )
        assert response.status_code == 422


class TestUserDelete:
    """Test user deletion endpoint (DELETE /api/v1/users/{user_id})."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self, client: AsyncClient) -> None:
        """Test successful user deletion."""
        user = await create_user(client)
        
        response = await client.delete(f"/api/v1/users/{user['id']}")
        
        assert response.status_code == 204
        
        # Verify user is deleted
        get_response = await client.get(f"/api/v1/users/{user['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent user returns 404."""
        response = await client.delete("/api/v1/users/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_cascades_profiles(self, client: AsyncClient) -> None:
        """Test that deleting user cascades to delete profiles."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        # Delete the user
        response = await client.delete(f"/api/v1/users/{user['id']}")
        assert response.status_code == 204
        
        # Verify profile is also deleted (FK cascade)
        profile_response = await client.get(f"/api/v1/profiles/{profile['id']}")
        assert profile_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_cascades_follows(self, client: AsyncClient) -> None:
        """Test that deleting follower user cascades to delete follows."""
        follower = await create_user(client)
        owner = await create_user(client)
        profile = await create_profile(client, owner["id"])
        follow = await create_follow(client, follower["id"], profile["id"])
        
        # Delete the follower
        response = await client.delete(f"/api/v1/users/{follower['id']}")
        assert response.status_code == 204
        
        # Verify follow is also deleted (FK cascade)
        follow_response = await client.get(f"/api/v1/follows/{follow['id']}")
        assert follow_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_cascades_channels(self, client: AsyncClient) -> None:
        """Test that deleting user cascades to delete their channels."""
        user = await create_user(client)
        profile = await create_profile(client, user["id"])
        
        # Create a channel under the profile
        channel_response = await client.post(
            "/api/v1/channels",
            json={
                "profile_id": profile["id"],
                "channel_name": "TestChannel"
            }
        )
        assert channel_response.status_code == 201
        channel_id = channel_response.json()["id"]
        
        # Delete the user
        delete_response = await client.delete(f"/api/v1/users/{user['id']}")
        assert delete_response.status_code == 204
        
        # Verify channel is also deleted (cascades through profile)
        channel_get = await client.get(f"/api/v1/channels/{channel_id}")
        assert channel_get.status_code == 404


class TestUserWorkflows:
    """Test realistic multi-step user workflows."""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, client: AsyncClient) -> None:
        """Test typical user registration workflow: create -> retrieve -> list."""
        # Create user
        user = await create_user(client)
        
        # Retrieve the created user
        get_response = await client.get(f"/api/v1/users/{user['id']}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == user["id"]
        
        # List users to verify new user is included
        list_response = await client.get("/api/v1/users?size=100")
        assert list_response.status_code == 200
        page = list_response.json()
        user_ids = [u["id"] for u in page["items"]]
        assert user["id"] in user_ids

    @pytest.mark.asyncio
    async def test_user_profile_update_flow(self, client: AsyncClient) -> None:
        """Test user update workflow: create -> update -> verify."""
        user = await create_user(client)
        n = TestDataGenerator.next_id()
        
        # Update user
        patch_response = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={"username": f"updated_{n}"}
        )
        assert patch_response.status_code == 200
        
        # Verify update persisted
        get_response = await client.get(f"/api/v1/users/{user['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["username"] == f"updated_{n}"
