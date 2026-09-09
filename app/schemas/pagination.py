"""Схемы и параметры пагинации коллекций.

Соответствует правилам STD-COL-01…STD-COL-06 стандарта API_STANDARD:
единые параметры ``offset`` и ``limit`` и единый конверт ответа.
"""

from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

ItemT = TypeVar("ItemT")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class Page(BaseModel, Generic[ItemT]):
    """Конверт ответа для любой коллекции публичного API."""

    items: list[ItemT] = Field(description="Записи текущей страницы")
    total: int = Field(description="Общее количество записей, доступных запросу", ge=0)
    offset: int = Field(description="Смещение текущей страницы от начала коллекции", ge=0)
    limit: int = Field(description="Запрошенный размер страницы", ge=1, le=MAX_LIMIT)


class PaginationParams(BaseModel):
    """Параметры постраничного обхода коллекции."""

    offset: int = 0
    limit: int = DEFAULT_LIMIT


def pagination_params(
    offset: Annotated[
        int,
        Query(ge=0, description="Смещение от начала коллекции"),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_LIMIT,
            description=f"Размер страницы, максимум {MAX_LIMIT}",
        ),
    ] = DEFAULT_LIMIT,
) -> PaginationParams:
    """Собрать параметры пагинации из query-строки.

    Args:
        offset: Смещение от начала коллекции.
        limit: Количество записей на странице.

    Returns:
        Проверенные параметры постраничного обхода.
    """
    return PaginationParams(offset=offset, limit=limit)
