"""ProfileChannel CRUD module.

Exposes a singleton ``profile_channel_crud`` that extends ``CRUDBase`` with
ProfileChannel-specific filter helpers.
"""

from __future__ import annotations

from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.profile_channel import ProfileChannel
from app.schemas.profile_channel import ProfileChannelCreate, ProfileChannelUpdate


class CRUDProfileChannel(
    CRUDBase[ProfileChannel, ProfileChannelCreate, ProfileChannelUpdate]
):
    """ProfileChannel-specific CRUD with extra filter helpers."""

    async def get_by_profile(
        self,
        db: AsyncSession,
        profile_id: int,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ProfileChannel], int]:
        """Return all channels belonging to *profile_id* with pagination."""
        return await self.get_multi(
            db, offset=offset, limit=limit, filters={"profile_id": profile_id}
        )


profile_channel_crud = CRUDProfileChannel(ProfileChannel)
