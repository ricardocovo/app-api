"""Pydantic v2 schemas for the ProfileChannel entity."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProfileChannelBase(BaseModel):
    """Fields shared by all ProfileChannel schema variants."""

    youtube_channel_id: str
    channel_title: str
    thumbnail_url: Optional[str] = None


class ProfileChannelCreate(ProfileChannelBase):
    """Fields required to create a new ProfileChannel."""

    profile_id: UUID


class ProfileChannelUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    youtube_channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    thumbnail_url: Optional[str] = None


class ProfileChannelRead(ProfileChannelBase):
    """Full ProfileChannel record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
