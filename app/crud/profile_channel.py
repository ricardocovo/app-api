"""CRUD operations for the ProfileChannel entity."""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_channel import ProfileChannel
from app.schemas.pagination import PaginationParams
from app.schemas.profile_channel import ProfileChannelCreate, ProfileChannelUpdate


async def get_channels(
    db: AsyncSession,
    params: PaginationParams,
    profile_id: Optional[int] = None,
) -> Tuple[list[ProfileChannel], int]:
    """Return a paginated list of channels with optional profile_id filter."""
    query = select(ProfileChannel)
    count_query = select(func.count()).select_from(ProfileChannel)

    if profile_id is not None:
        query = query.where(ProfileChannel.profile_id == profile_id)
        count_query = count_query.where(ProfileChannel.profile_id == profile_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(params.offset).limit(params.size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_channel(
    db: AsyncSession, channel_id: int
) -> Optional[ProfileChannel]:
    """Return a single channel by ID, or None if not found."""
    result = await db.execute(
        select(ProfileChannel).where(ProfileChannel.id == channel_id)
    )
    return result.scalar_one_or_none()


async def create_channel(
    db: AsyncSession, data: ProfileChannelCreate
) -> ProfileChannel:
    """Create a new channel. Raises IntegrityError on FK violation."""
    channel = ProfileChannel(
        profile_id=data.profile_id,
        channel_name=data.channel_name,
        channel_url=str(data.channel_url) if data.channel_url is not None else None,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


async def update_channel(
    db: AsyncSession, channel_id: int, data: ProfileChannelUpdate
) -> Optional[ProfileChannel]:
    """Apply a partial update to a channel. Returns None if not found."""
    channel = await get_channel(db, channel_id)
    if channel is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    if "channel_url" in updates and updates["channel_url"] is not None:
        updates["channel_url"] = str(updates["channel_url"])

    for field, value in updates.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)
    return channel


async def delete_channel(db: AsyncSession, channel_id: int) -> bool:
    """Delete a channel by ID. Returns False if not found."""
    channel = await get_channel(db, channel_id)
    if channel is None:
        return False

    await db.delete(channel)
    await db.commit()
    return True
