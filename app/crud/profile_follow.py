"""ProfileFollow CRUD module.

Exposes a singleton ``profile_follow_crud`` that extends ``CRUDBase`` with
ProfileFollow-specific filter helpers.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.profile_follow import ProfileFollow
from app.schemas.profile_follow import ProfileFollowCreate, ProfileFollowUpdate


class CRUDProfileFollow(
    CRUDBase[ProfileFollow, ProfileFollowCreate, ProfileFollowUpdate]
):
    """ProfileFollow-specific CRUD with extra filter helpers."""

    async def get_by_follower(
        self,
        db: AsyncSession,
        follower_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ProfileFollow], int]:
        """Return all follows initiated by *follower_id* with pagination."""
        return await self.get_multi(
            db, offset=offset, limit=limit, filters={"follower_id": follower_id}
        )

    async def get_by_profile(
        self,
        db: AsyncSession,
        profile_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ProfileFollow], int]:
        """Return all follows targeting *profile_id* with pagination."""
        return await self.get_multi(
            db, offset=offset, limit=limit, filters={"profile_id": profile_id}
        )

    async def get_by_follower_and_profile(
        self,
        db: AsyncSession,
        follower_id: int,
        profile_id: int,
    ) -> Optional[ProfileFollow]:
        """Return the follow record for a specific (follower, profile) pair."""
        result = await db.execute(
            select(ProfileFollow).where(
                ProfileFollow.follower_id == follower_id,
                ProfileFollow.profile_id == profile_id,
            )
        )
        return result.scalars().first()


profile_follow_crud = CRUDProfileFollow(ProfileFollow)
