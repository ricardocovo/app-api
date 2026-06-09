"""ProfileFollow ORM model.

ERD camelCase fields map to snake_case Python attributes:
  id         → id
  followerId → follower_id
  profileId  → profile_id
  createdAt  → created_at
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.user import User


class ProfileFollow(Base):
    """Records that a user (follower) follows a profile."""

    __tablename__ = "profile_follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "profile_id", name="uq_profile_follow"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    follower: Mapped["User"] = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="following",
    )
    profile: Mapped["Profile"] = relationship(
        "Profile",
        foreign_keys=[profile_id],
        back_populates="follows",
    )
