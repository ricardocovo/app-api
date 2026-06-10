"""Profile ORM model.

ERD camelCase fields map to snake_case Python attributes:
  id          → id
  userId      → user_id
  displayName → display_name
  bio         → bio
  createdAt   → created_at
  updatedAt   → updated_at
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile_channel import ProfileChannel
    from app.models.profile_follow import ProfileFollow
    from app.models.user import User


class Profile(Base):
    """A user-owned profile (a user may own multiple profiles)."""

    __tablename__ = "profile"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        "userId", Uuid(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_default: Mapped[bool] = mapped_column("isDefault", Boolean, nullable=False, default=False)
    is_public: Mapped[bool] = mapped_column("isPublic", Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profiles")
    follows: Mapped[List["ProfileFollow"]] = relationship(
        "ProfileFollow",
        foreign_keys="ProfileFollow.profile_id",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    channels: Mapped[List["ProfileChannel"]] = relationship(
        "ProfileChannel", back_populates="profile", cascade="all, delete-orphan"
    )
