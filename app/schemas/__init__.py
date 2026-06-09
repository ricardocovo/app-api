"""Pydantic v2 schemas package – re-exports all schema classes."""

from app.schemas.pagination import Page, PaginationParams
from app.schemas.profile import ProfileBase, ProfileCreate, ProfileRead, ProfileUpdate
from app.schemas.profile_channel import (
    ProfileChannelBase,
    ProfileChannelCreate,
    ProfileChannelRead,
    ProfileChannelUpdate,
)
from app.schemas.profile_follow import (
    ProfileFollowBase,
    ProfileFollowCreate,
    ProfileFollowRead,
    ProfileFollowUpdate,
)
from app.schemas.user import UserBase, UserCreate, UserRead, UserUpdate

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    # Profile
    "ProfileBase",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileRead",
    # ProfileFollow
    "ProfileFollowBase",
    "ProfileFollowCreate",
    "ProfileFollowUpdate",
    "ProfileFollowRead",
    # ProfileChannel
    "ProfileChannelBase",
    "ProfileChannelCreate",
    "ProfileChannelUpdate",
    "ProfileChannelRead",
    # Pagination
    "PaginationParams",
    "Page",
]
