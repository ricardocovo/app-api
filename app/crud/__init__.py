"""CRUD package – re-exports the generic base and all CRUD functions."""

from app.crud.base import CRUDBase
from app.crud.profile import (
    create_profile,
    delete_profile,
    get_profile,
    get_profiles,
    update_profile,
)
from app.crud.profile_channel import (
    create_channel,
    delete_channel,
    get_channel,
    get_channels,
    update_channel,
)
from app.crud.profile_follow import (
    create_follow,
    delete_follow,
    get_follow,
    get_follows,
)
from app.crud.user import (
    create_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)

__all__ = [
    # Generic base
    "CRUDBase",
    # User
    "get_users",
    "get_user",
    "create_user",
    "update_user",
    "delete_user",
    # Profile
    "get_profiles",
    "get_profile",
    "create_profile",
    "update_profile",
    "delete_profile",
    # ProfileFollow
    "get_follows",
    "get_follow",
    "create_follow",
    "delete_follow",
    # ProfileChannel
    "get_channels",
    "get_channel",
    "create_channel",
    "update_channel",
    "delete_channel",
]

