"""CRUD package – re-exports all CRUD singletons and the generic base."""

from app.crud.base import CRUDBase
from app.crud.profile import profile_crud
from app.crud.profile_channel import profile_channel_crud
from app.crud.profile_follow import profile_follow_crud
from app.crud.user import user_crud

__all__ = [
    "CRUDBase",
    "user_crud",
    "profile_crud",
    "profile_follow_crud",
    "profile_channel_crud",
]
