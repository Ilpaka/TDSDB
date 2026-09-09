"""Базовые классы схем публичного API.

Модуль задаёт общее поведение всех схем ответа: сериализацию даты и времени
в формате RFC 3339 (UTC) согласно правилу STD-DATA-04 стандарта API_STANDARD.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class APISchema(BaseModel):
    """Базовая схема публичного контракта.

    Все схемы ответа наследуются от этого класса, чтобы дата и время
    сериализовались единообразно, независимо от того, вернуло ли хранилище
    значение с информацией о часовом поясе.
    """

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json")
    def _serialize_datetime(self, value: object) -> object:
        """Привести значения даты и времени к RFC 3339 в UTC.

        SQLite возвращает ``datetime`` без сведений о часовом поясе, поэтому
        naive-значения трактуются как UTC.

        Args:
            value: Произвольное значение поля схемы.

        Returns:
            Строка вида ``2026-09-09T08:15:30Z`` для даты и времени;
            исходное значение для остальных типов.
        """
        if not isinstance(value, datetime):
            return value

        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
