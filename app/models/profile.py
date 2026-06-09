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

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile_channel import ProfileChannel
    from app.models.profile_follow import ProfileFollow
    from app.models.user import User


class Profile(Base):
    """A user-owned profile (a user may own multiple profiles)."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
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
