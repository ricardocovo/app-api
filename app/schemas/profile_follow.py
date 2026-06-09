"""Pydantic v2 schemas for the ProfileFollow entity."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileFollowBase(BaseModel):
    """Fields shared by all ProfileFollow schema variants."""

    follower_id: int
    profile_id: int


class ProfileFollowCreate(ProfileFollowBase):
    """Fields required to create a new ProfileFollow.

    Both FKs are required at creation; server-generated fields are excluded.
    """


class ProfileFollowUpdate(BaseModel):
    """Placeholder for partial PATCH updates.

    ProfileFollow records are effectively immutable (the FK pair is unique),
    so no fields are updatable.  The schema exists for API consistency.
    """


class ProfileFollowRead(ProfileFollowBase):
    """Full ProfileFollow record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
