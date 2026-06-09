"""CRUD operations for the User entity."""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.schemas.user import UserCreate, UserUpdate


async def get_users(
    db: AsyncSession,
    params: PaginationParams,
    email: Optional[str] = None,
) -> Tuple[list[User], int]:
    """Return a paginated list of users with optional email filter."""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if email is not None:
        query = query.where(User.email == email)
        count_query = count_query.where(User.email == email)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(params.offset).limit(params.size)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Return a single user by ID, or None if not found."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Create a new user. Raises IntegrityError on duplicate email/username."""
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession, user_id: int, data: UserUpdate
) -> Optional[User]:
    """Apply a partial update to a user. Returns None if not found."""
    user = await get_user(db, user_id)
    if user is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete a user by ID. Returns False if not found."""
    user = await get_user(db, user_id)
    if user is None:
        return False

    await db.delete(user)
    await db.commit()
    return True
