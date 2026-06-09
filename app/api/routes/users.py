"""API routes for the User entity."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user, delete_user, get_user, get_users, update_user
from app.db.session import get_db
from app.schemas.pagination import Page, PaginationParams
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserRead])
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    email: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[UserRead]:
    params = PaginationParams(page=page, size=size)
    items, total = await get_users(db, params, email=email)
    return Page.create(items=items, total=total, params=params)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    try:
        return await create_user(db, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with the given email or username already exists.",
        ) from exc


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    try:
        user = await update_user(db, user_id, data)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with the given email or username already exists.",
        ) from exc
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
