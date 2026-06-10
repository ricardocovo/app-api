"""ProfileFollow ORM model.

ERD camelCase fields map to snake_case Python attributes:
  id         → id
  followerId → follower_id
  profileId  → profile_id
  createdAt  → created_at
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.user import User


class ProfileFollow(Base):
    """Records that a user (follower) follows a profile."""

    __tablename__ = "profile_follow"
    __table_args__ = (
        UniqueConstraint("followerId", "profileId", name="uq_profile_follow"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id: Mapped[uuid.UUID] = mapped_column(
        "followerId", Uuid(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        "profileId", Uuid(as_uuid=True), ForeignKey("profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", server_default=func.now(), nullable=False
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
