"""User ORM model.

ERD camelCase fields map to snake_case Python attributes:
  id           → id
  username     → username
  email        → email
  passwordHash → password_hash
  createdAt    → created_at

Intentionally excluded this iteration: accessToken, refreshToken.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.profile_follow import ProfileFollow


class User(Base):
    """Registered user account."""

    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[Optional[str]] = mapped_column("googleId", String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column("avatarUrl", String(2048), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column("accessToken", String(2048), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column("refreshToken", String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    profiles: Mapped[List["Profile"]] = relationship(
        "Profile", back_populates="user", cascade="all, delete-orphan"
    )
    following: Mapped[List["ProfileFollow"]] = relationship(
        "ProfileFollow",
        foreign_keys="ProfileFollow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan",
    )
