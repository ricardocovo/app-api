"""Integration smoke tests for API routes."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_user_profile_follow_channel_flow(client: AsyncClient) -> None:
    # Create two users
    user1 = (
        await client.post(
            "/api/v1/users",
            json={"email": "route1@example.com", "name": "Route One", "google_id": "g_route_1"},
        )
    ).json()
    user2 = (
        await client.post(
            "/api/v1/users",
            json={"email": "route2@example.com", "name": "Route Two", "google_id": "g_route_2"},
        )
    ).json()

    # Create profile
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={"user_id": user2["id"], "name": "Route Profile", "is_public": True},
    )
    assert profile_resp.status_code == 201
    profile = profile_resp.json()

    # Create follow
    follow_resp = await client.post(
        "/api/v1/follows",
        json={"follower_id": user1["id"], "profile_id": profile["id"]},
    )
    assert follow_resp.status_code == 201
    follow = follow_resp.json()

    # Create channel
    channel_resp = await client.post(
        "/api/v1/channels",
        json={
            "profile_id": profile["id"],
            "youtube_channel_id": "yt_route",
            "channel_title": "Route Channel",
            "thumbnail_url": "https://example.com/route.png",
        },
    )
    assert channel_resp.status_code == 201
    channel = channel_resp.json()

    # Read resources
    assert (await client.get(f"/api/v1/users/{user1['id']}")).status_code == 200
    assert (await client.get(f"/api/v1/profiles/{profile['id']}")).status_code == 200
    assert (await client.get(f"/api/v1/follows/{follow['id']}")).status_code == 200
    assert (await client.get(f"/api/v1/channels/{channel['id']}")).status_code == 200

    # List resources
    assert (await client.get("/api/v1/users?page=1&size=10")).status_code == 200
    assert (await client.get("/api/v1/profiles?page=1&size=10")).status_code == 200
    assert (await client.get("/api/v1/follows?page=1&size=10")).status_code == 200
    assert (await client.get("/api/v1/channels?page=1&size=10")).status_code == 200

    # Update resources
    patch_user = await client.patch(f"/api/v1/users/{user1['id']}", json={"name": "Route One Updated"})
    assert patch_user.status_code == 200

    patch_profile = await client.patch(
        f"/api/v1/profiles/{profile['id']}", json={"name": "Route Profile Updated"}
    )
    assert patch_profile.status_code == 200

    patch_channel = await client.patch(
        f"/api/v1/channels/{channel['id']}", json={"channel_title": "Route Channel Updated"}
    )
    assert patch_channel.status_code == 200

    # Delete resources
    assert (await client.delete(f"/api/v1/follows/{follow['id']}")).status_code == 204
    assert (await client.delete(f"/api/v1/channels/{channel['id']}")).status_code == 204
    assert (await client.delete(f"/api/v1/profiles/{profile['id']}")).status_code == 204
    assert (await client.delete(f"/api/v1/users/{user1['id']}")).status_code == 204


@pytest.mark.asyncio
async def test_not_found_and_validation(client: AsyncClient) -> None:
    missing_id = str(uuid.uuid4())

    assert (await client.get(f"/api/v1/users/{missing_id}")).status_code == 404
    assert (await client.get(f"/api/v1/profiles/{missing_id}")).status_code == 404
    assert (await client.get(f"/api/v1/follows/{missing_id}")).status_code == 404
    assert (await client.get(f"/api/v1/channels/{missing_id}")).status_code == 404

    assert (await client.get("/api/v1/users/invalid")).status_code == 422
    assert (await client.get("/api/v1/profiles/invalid")).status_code == 422
    assert (await client.get("/api/v1/follows/invalid")).status_code == 422
    assert (await client.get("/api/v1/channels/invalid")).status_code == 422
