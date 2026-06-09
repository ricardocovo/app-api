"""Pydantic v2 schemas for the ProfileChannel entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class ProfileChannelBase(BaseModel):
    """Fields shared by all ProfileChannel schema variants."""

    channel_name: str
    channel_url: Optional[HttpUrl] = None


class ProfileChannelCreate(ProfileChannelBase):
    """Fields required to create a new ProfileChannel.

    ``profile_id`` is required at creation; server-generated fields are excluded.
    """

    profile_id: int


class ProfileChannelUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    channel_name: Optional[str] = None
    channel_url: Optional[HttpUrl] = None


class ProfileChannelRead(ProfileChannelBase):
    """Full ProfileChannel record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime
