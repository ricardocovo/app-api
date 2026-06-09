"""Pydantic v2 schemas for the Profile entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    """Fields shared by all Profile schema variants."""

    display_name: str
    bio: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Fields required to create a new Profile.

    ``user_id`` is required at creation; server-generated fields are excluded.
    """

    user_id: int


class ProfileUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    display_name: Optional[str] = None
    bio: Optional[str] = None


class ProfileRead(ProfileBase):
    """Full Profile record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
