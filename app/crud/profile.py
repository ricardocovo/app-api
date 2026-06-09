"""CRUD operations for the Profile entity."""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.schemas.pagination import PaginationParams
from app.schemas.profile import ProfileCreate, ProfileUpdate


async def get_profiles(
    db: AsyncSession,
    params: PaginationParams,
    user_id: Optional[int] = None,
) -> Tuple[list[Profile], int]:
    """Return a paginated list of profiles with optional user_id filter."""
    query = select(Profile)
    count_query = select(func.count()).select_from(Profile)

    if user_id is not None:
        query = query.where(Profile.user_id == user_id)
        count_query = count_query.where(Profile.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(params.offset).limit(params.size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_profile(db: AsyncSession, profile_id: int) -> Optional[Profile]:
    """Return a single profile by ID, or None if not found."""
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    return result.scalar_one_or_none()


async def create_profile(db: AsyncSession, data: ProfileCreate) -> Profile:
    """Create a new profile. Raises IntegrityError on FK violation."""
    profile = Profile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(
    db: AsyncSession, profile_id: int, data: ProfileUpdate
) -> Optional[Profile]:
    """Apply a partial update to a profile. Returns None if not found."""
    profile = await get_profile(db, profile_id)
    if profile is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


async def delete_profile(db: AsyncSession, profile_id: int) -> bool:
    """Delete a profile by ID. Returns False if not found."""
    profile = await get_profile(db, profile_id)
    if profile is None:
        return False

    await db.delete(profile)
    await db.commit()
    return True
