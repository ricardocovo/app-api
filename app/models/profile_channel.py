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

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class ProfileChannel(Base):
    """A communication channel (e.g. social link) attached to a profile."""

    __tablename__ = "profile_channel"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        "profileId", Uuid(as_uuid=True), ForeignKey("profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    youtube_channel_id: Mapped[str] = mapped_column("youtubeChannelId", String(255), nullable=False)
    channel_title: Mapped[str] = mapped_column("channelTitle", String(255), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column("thumbnailUrl", String(2048), nullable=True)

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="channels")
