"""CRUD operations for the ProfileFollow entity."""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_follow import ProfileFollow
from app.schemas.pagination import PaginationParams
from app.schemas.profile_follow import ProfileFollowCreate


async def get_follows(
    db: AsyncSession,
    params: PaginationParams,
    follower_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> Tuple[list[ProfileFollow], int]:
    """Return a paginated list of follows with optional filters."""
    query = select(ProfileFollow)
    count_query = select(func.count()).select_from(ProfileFollow)

    if follower_id is not None:
        query = query.where(ProfileFollow.follower_id == follower_id)
        count_query = count_query.where(ProfileFollow.follower_id == follower_id)

    if profile_id is not None:
        query = query.where(ProfileFollow.profile_id == profile_id)
        count_query = count_query.where(ProfileFollow.profile_id == profile_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(params.offset).limit(params.size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_follow(db: AsyncSession, follow_id: int) -> Optional[ProfileFollow]:
    """Return a single follow by ID, or None if not found."""
    result = await db.execute(
        select(ProfileFollow).where(ProfileFollow.id == follow_id)
    )
    return result.scalar_one_or_none()


async def create_follow(
    db: AsyncSession, data: ProfileFollowCreate
) -> ProfileFollow:
    """Create a new follow record. Raises IntegrityError on duplicate or FK violation."""
    follow = ProfileFollow(**data.model_dump())
    db.add(follow)
    await db.commit()
    await db.refresh(follow)
    return follow


async def delete_follow(db: AsyncSession, follow_id: int) -> bool:
    """Delete a follow by ID. Returns False if not found."""
    follow = await get_follow(db, follow_id)
    if follow is None:
        return False

    await db.delete(follow)
    await db.commit()
    return True
