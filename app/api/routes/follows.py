"""API routes for the ProfileFollow entity.

ProfileFollow omits PATCH – create/delete only.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.profile_follow import create_follow, delete_follow, get_follow, get_follows
from app.db.session import get_db
from app.schemas.pagination import Page, PaginationParams
from app.schemas.profile_follow import ProfileFollowCreate, ProfileFollowRead

router = APIRouter(prefix="/follows", tags=["follows"])


@router.get("", response_model=Page[ProfileFollowRead])
async def list_follows(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    follower_id: Optional[UUID] = Query(default=None),
    profile_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[ProfileFollowRead]:
    params = PaginationParams(page=page, size=size)
    items, total = await get_follows(db, params, follower_id=follower_id, profile_id=profile_id)
    return Page.create(items=items, total=total, params=params)


@router.get("/{follow_id}", response_model=ProfileFollowRead)
async def read_follow(
    follow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ProfileFollowRead:
    follow = await get_follow(db, follow_id)
    if follow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")
    return follow


@router.post("", response_model=ProfileFollowRead, status_code=status.HTTP_201_CREATED)
async def create_new_follow(
    data: ProfileFollowCreate,
    db: AsyncSession = Depends(get_db),
) -> ProfileFollowRead:
    try:
        return await create_follow(db, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Follow already exists or referenced user/profile does not exist.",
        ) from exc


@router.delete("/{follow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_follow(
    follow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await delete_follow(db, follow_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")
