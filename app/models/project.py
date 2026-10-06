"""Модель проекта."""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

class Project(SQLModel, table=True):
    """Проект — контейнер документов и единица разграничения доступа."""

    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=120, min_length=3)
    description: Optional[str] = Field(default=None)
    owner_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    owner: "User" = Relationship(back_populates="owner_projects")

    accesses: list["ProjectAccess"] = Relationship(back_populates="project")
    documents: list["Document"] = Relationship(back_populates="project")



if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project_access import ProjectAccess
    from app.models.document import Document