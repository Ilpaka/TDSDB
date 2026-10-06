"""Базовые типы и классы схем публичного API.

Модуль задаёт сериализацию даты и времени в формате RFC 3339 (UTC) согласно
правилу STD-DATA-04 стандарта API_STANDARD. Сериализатор привязан к типу
:data:`UTCDateTime`, а не ко всем полям схемы, поэтому OpenAPI сохраняет
точные типы полей (``integer``, ``string`` с ``format: date-time`` и т. д.).
"""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer, WithJsonSchema


def to_rfc3339_utc(value: datetime) -> str:
    """Привести дату и время к RFC 3339 в UTC.

    SQLite возвращает ``datetime`` без сведений о часовом поясе, поэтому
    naive-значения трактуются как UTC.

    Args:
        value: Дата и время.

    Returns:
        Строка вида ``2026-09-09T08:15:30Z``.
    """
    moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UTCDateTime = Annotated[
    datetime,
    PlainSerializer(to_rfc3339_utc, return_type=str, when_used="json"),
    WithJsonSchema(
        {"type": "string", "format": "date-time", "examples": ["2026-09-09T08:15:30Z"]},
        mode="serialization",
    ),
]
"""Дата и время, сериализуемые в RFC 3339 UTC с суффиксом ``Z``."""


class APISchema(BaseModel):
    """Базовая схема ответа публичного контракта.

    Разрешает построение схемы из атрибутов ORM-моделей.
    """

    model_config = ConfigDict(from_attributes=True)
