"""API routes for the Profile entity."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.profile import (
    create_profile,
    delete_profile,
    get_profile,
    get_profiles,
    update_profile,
)
from app.db.session import get_db
from app.schemas.pagination import Page, PaginationParams
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=Page[ProfileRead])
async def list_profiles(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user_id: Optional[UUID] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[ProfileRead]:
    params = PaginationParams(page=page, size=size)
    items, total = await get_profiles(db, params, user_id=user_id)
    return Page.create(items=items, total=total, params=params)


@router.get("/{profile_id}", response_model=ProfileRead)
async def read_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    profile = await get_profile(db, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_new_profile(
    data: ProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    try:
        return await create_profile(db, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid user_id or a conflicting profile already exists.",
        ) from exc


@router.patch("/{profile_id}", response_model=ProfileRead)
async def patch_profile(
    profile_id: UUID,
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    try:
        profile = await update_profile(db, profile_id, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict while updating profile.",
        ) from exc
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await delete_profile(db, profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
