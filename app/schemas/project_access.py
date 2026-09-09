"""Схемы управления доступом к проектам."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.project_access import Permission
from app.schemas.base import APISchema


class ProjectAccessUpsert(BaseModel):
    """Тело запроса на выдачу или изменение доступа."""

    permission: Permission = Field(
        default=Permission.viewer,
        description="Уровень доступа участника к проекту",
        examples=["editor"],
    )


class ProjectAccessRead(APISchema):
    """Запись о выданном доступе."""

    id: int = Field(description="Идентификатор записи о доступе")
    project_id: int = Field(description="Идентификатор проекта")
    user_id: int = Field(description="Идентификатор участника")
    permission: Permission = Field(description="Уровень доступа")
    granted_by: int = Field(description="Идентификатор пользователя, выдавшего доступ")
    created_at: datetime = Field(description="Момент выдачи доступа")


class ProjectAccessReadWithUser(ProjectAccessRead):
    """Запись о доступе с адресами участника и выдавшего доступ."""

    user_email: Optional[str] = Field(default=None, description="Адрес участника")
    granter_email: Optional[str] = Field(
        default=None, description="Адрес пользователя, выдавшего доступ"
    )
