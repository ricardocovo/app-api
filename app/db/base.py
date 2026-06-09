from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so that Alembic autogenerate can discover them.
# Uncomment each line as the model file is created in Phase 2.
# from app.models import user, profile, profile_follow, profile_channel  # noqa: F401
