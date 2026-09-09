"""Схемы журнала действий пользователей."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.audit_log import EntityType
from app.schemas.base import APISchema


class AuditLogBase(APISchema):
    """Общие поля записи журнала."""

    action: str = Field(description="Выполненное действие", examples=["grant_access"])
    entity_type: EntityType = Field(description="Тип сущности, к которой относится действие")
    entity_id: Optional[int] = Field(default=None, description="Идентификатор сущности")
    meta: Optional[str] = Field(default=None, description="Дополнительные сведения в формате JSON")


class AuditLogCreate(AuditLogBase):
    """Запись, добавляемая в журнал."""

    user_id: int = Field(description="Идентификатор пользователя, выполнившего действие")


class AuditLogRead(AuditLogBase):
    """Запись журнала."""

    id: int = Field(description="Идентификатор записи")
    user_id: int = Field(description="Идентификатор пользователя, выполнившего действие")
    created_at: datetime = Field(description="Момент выполнения действия")


class AuditLogReadWithUser(AuditLogRead):
    """Запись журнала с адресом пользователя."""

    user_email: Optional[str] = Field(
        default=None, description="Адрес пользователя, выполнившего действие"
    )


class AuditLogFilter(BaseModel):
    """Условия отбора записей журнала."""

    date_from: Optional[date] = None
    date_to: Optional[date] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[EntityType] = None
