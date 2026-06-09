"""Generic async CRUD base class.

``CRUDBase[ModelType, CreateSchema, UpdateSchema]`` provides the five standard
CRUD operations using SQLAlchemy 2.0 async-style ``select()`` queries.
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic async CRUD operations for a SQLAlchemy ORM model.

    Type parameters
    ---------------
    ModelType
        The SQLAlchemy ORM model class.
    CreateSchemaType
        Pydantic schema used for ``create`` (must expose ``.model_dump()``).
    UpdateSchemaType
        Pydantic schema used for ``update`` (must expose
        ``.model_dump(exclude_unset=True)`` for partial PATCH semantics).
    """

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Return the record with the given primary key, or ``None``."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[ModelType], int]:
        """Return a paginated slice and the total matching count.

        Parameters
        ----------
        db:
            Active async database session.
        offset:
            Number of rows to skip (SQL ``OFFSET``).
        limit:
            Maximum rows to return (SQL ``LIMIT``).
        filters:
            Optional ``{column_name: value}`` equality filters applied to
            both the data query and the count query.

        Returns
        -------
        Tuple[List[ModelType], int]
            ``(rows, total_count)`` where *total_count* reflects all matching
            rows before pagination.
        """
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            for attr, value in filters.items():
                column = getattr(self.model, attr)
                query = query.where(column == value)
                count_query = count_query.where(column == value)

        total_result = await db.execute(count_query)
        total: int = total_result.scalar_one()

        data_result = await db.execute(query.offset(offset).limit(limit))
        rows: List[ModelType] = list(data_result.scalars().all())

        return rows, total

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        """Insert a new row and return the persisted ORM object."""
        # Use mode="json" so that Pydantic-specific URL / enum types are
        # coerced to plain Python strings/values that every DB driver accepts.
        data: Dict[str, Any] = (
            obj_in.model_dump(mode="json")  # type: ignore[union-attr]
            if hasattr(obj_in, "model_dump")
            else dict(obj_in)  # type: ignore[call-overload]
        )
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Apply a partial update to *db_obj* and return the updated object.

        Accepts either a Pydantic ``*Update`` schema instance (uses
        ``model_dump(exclude_unset=True)`` for PATCH semantics) or a plain
        ``dict``.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)  # type: ignore[union-attr]

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Delete the record with the given primary key.

        Returns the deleted object (pre-deletion state), or ``None`` if not
        found.
        """
        db_obj = await self.get(db, id)
        if db_obj is None:
            return None
        await db.delete(db_obj)
        await db.commit()
        return db_obj
