"""Shared pagination utilities.

``PaginationParams`` captures ``page`` / ``size`` query parameters.
``Page[T]`` is a generic response wrapper returned by list endpoints.
"""

from __future__ import annotations

import math
from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query-parameter schema for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="1-based page number.")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100).")

    @property
    def offset(self) -> int:
        """Return the SQL OFFSET value for this page."""
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: List[T]
    total: int = Field(description="Total number of items across all pages.")
    page: int = Field(description="Current page number (1-based).")
    size: int = Field(description="Number of items per page.")
    pages: int = Field(description="Total number of pages.")

    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams) -> "Page[T]":
        """Convenience constructor from a result list and pagination params."""
        pages = max(1, math.ceil(total / params.size))
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
