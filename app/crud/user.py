"""User CRUD module.

Exposes a singleton ``user_crud`` that extends ``CRUDBase`` with
User-specific filter helpers.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """User-specific CRUD with extra lookup helpers."""

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Return the user with the given email address, or ``None``."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(
        self, db: AsyncSession, username: str
    ) -> Optional[User]:
        """Return the user with the given username, or ``None``."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()


user_crud = CRUDUser(User)
