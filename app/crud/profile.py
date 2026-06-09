"""Profile CRUD module.

Exposes a singleton ``profile_crud`` that extends ``CRUDBase`` with
Profile-specific filter helpers.
"""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class CRUDProfile(CRUDBase[Profile, ProfileCreate, ProfileUpdate]):
    """Profile-specific CRUD with extra filter helpers."""

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Profile], int]:
        """Return all profiles owned by *user_id* with pagination."""
        return await self.get_multi(
            db, offset=offset, limit=limit, filters={"user_id": user_id}
        )


profile_crud = CRUDProfile(Profile)
