"""Pydantic v2 schemas for the User entity."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Fields shared by all User schema variants."""

    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """Fields required to create a new User."""

    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class UserUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class UserRead(UserBase):
    """Full User record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
