"""Модель доступа участника к проекту."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship

class Permission(str, Enum):
    """Уровень доступа к проекту: viewer (чтение) или editor (изменение)."""

    viewer = "viewer"
    editor = "editor"


class ProjectAccess(SQLModel, table=True):
    """Запись о доступе пользователя к проекту."""

    __tablename__ = "project_accesses"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    permission: Permission = Field(default=Permission.viewer)
    granted_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))

    project: "Project" = Relationship(back_populates="accesses")

    user: "User" = Relationship(
        back_populates="project_accesses",
        sa_relationship_kwargs={"foreign_keys": "[ProjectAccess.user_id]"}
    )

    granter: "User" = Relationship(
        back_populates="granted_access",
        sa_relationship_kwargs={"foreign_keys": "[ProjectAccess.granted_by]"}
    )



if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User