"""ProfileChannel ORM model.

ERD camelCase fields map to snake_case Python attributes:
  id          → id
  profileId   → profile_id
  channelName → channel_name
  channelUrl  → channel_url
  createdAt   → created_at
  updatedAt   → updated_at
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class ProfileChannel(Base):
    """A communication channel (e.g. social link) attached to a profile."""

    __tablename__ = "profile_channels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="channels")
