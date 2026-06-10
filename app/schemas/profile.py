"""Pydantic v2 schemas for the Profile entity."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileBase(BaseModel):
    """Fields shared by all Profile schema variants."""

    name: str
    is_default: bool = False
    is_public: bool = True


class ProfileCreate(ProfileBase):
    """Fields required to create a new Profile."""

    user_id: UUID


class ProfileUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    name: str | None = None
    is_default: bool | None = None
    is_public: bool | None = None


class ProfileRead(ProfileBase):
    """Full Profile record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
