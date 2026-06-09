from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so that Alembic autogenerate can discover them.
from app.models import profile, profile_channel, profile_follow, user  # noqa: F401
