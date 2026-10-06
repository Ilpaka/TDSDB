"""Модель документа проекта."""

from datetime import datetime, timezone

from typing import Optional, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship

class DocumentStatus(str, Enum):
    """Состояние жизненного цикла документа: draft, published или archived."""

    draft = "draft"
    published = "published"
    archived = "archived"


class Document(SQLModel, table=True):
    """Документ, принадлежащий проекту."""

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    title: str = Field(max_length=120, min_length=3)
    content: Optional[str] = Field(default="")
    status: DocumentStatus = Field(default=DocumentStatus.draft)
    created_by: int = Field(foreign_key="users.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))


    project: "Project" = Relationship(back_populates="documents")

    creator: "User" = Relationship(
        back_populates="created_documents",
        sa_relationship_kwargs={"foreign_keys": "[Document.created_by]"}
    )

    updater: Optional["User"] = Relationship(
        back_populates="updated_documents",
        sa_relationship_kwargs={"foreign_keys": "[Document.updated_by]"}
    )

    versions: list["DocumentVersion"] = Relationship(back_populates="document")


if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.document_version import DocumentVersion

