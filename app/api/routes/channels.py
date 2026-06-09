"""API routes for the ProfileChannel entity."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.profile_channel import (
    create_channel,
    delete_channel,
    get_channel,
    get_channels,
    update_channel,
)
from app.db.session import get_db
from app.schemas.pagination import Page, PaginationParams
from app.schemas.profile_channel import (
    ProfileChannelCreate,
    ProfileChannelRead,
    ProfileChannelUpdate,
)

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=Page[ProfileChannelRead])
async def list_channels(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    profile_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[ProfileChannelRead]:
    params = PaginationParams(page=page, size=size)
    items, total = await get_channels(db, params, profile_id=profile_id)
    return Page.create(items=items, total=total, params=params)


@router.get("/{channel_id}", response_model=ProfileChannelRead)
async def read_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProfileChannelRead:
    channel = await get_channel(db, channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


@router.post("", response_model=ProfileChannelRead, status_code=status.HTTP_201_CREATED)
async def create_new_channel(
    data: ProfileChannelCreate,
    db: AsyncSession = Depends(get_db),
) -> ProfileChannelRead:
    try:
        return await create_channel(db, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid profile_id or a conflicting channel already exists.",
        ) from exc


@router.patch("/{channel_id}", response_model=ProfileChannelRead)
async def patch_channel(
    channel_id: int,
    data: ProfileChannelUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProfileChannelRead:
    try:
        channel = await update_channel(db, channel_id, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict while updating channel.",
        ) from exc
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await delete_channel(db, channel_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
