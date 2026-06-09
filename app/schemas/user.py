"""Pydantic v2 schemas for the User entity.

API field names use snake_case throughout (matching the ORM attribute names).

Intentionally excluded:
- ``access_token`` / ``refresh_token`` – dropped for this iteration (no auth).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Fields shared by all User schema variants."""

    username: str
    email: EmailStr


class UserCreate(UserBase):
    """Fields required to create a new User.

    Server-generated fields (``id``, ``created_at``) are excluded.
    """

    password_hash: str


class UserUpdate(BaseModel):
    """All fields optional for partial PATCH updates."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None


class UserRead(UserBase):
    """Full User record returned by the API.

    ``password_hash`` is intentionally excluded from read responses.
    ``model_config`` enables ORM-mode serialisation.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
