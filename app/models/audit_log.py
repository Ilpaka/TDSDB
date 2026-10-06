"""Модель записи журнала действий."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship

class EntityType(str, Enum):
    """Тип сущности, к которой относится действие: user, project, document или access."""

    user = "user"
    project = "project"
    document = "document"
    access = "access"

class AuditLog(SQLModel, table=True):
    """Запись о действии пользователя."""

    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    action: str = Field(max_length=100)
    entity_type: EntityType
    entity_id: Optional[int] = Field(default=None)
    meta: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc), index=True)

    user: "User" = Relationship(back_populates="audit_logs")



if TYPE_CHECKING:
    from app.models.user import User