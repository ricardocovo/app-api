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

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.profile import Profile
    from app.models.profile_follow import ProfileFollow


class User(Base):
    """Registered user account."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
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
