"""Модель сохранённой версии документа."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship


class DocumentVersion(SQLModel, table=True):
    """Снимок содержимого документа с порядковым номером."""

    __tablename__ = "document_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", index=True)
    version: int = Field(default=1)
    content_snapshot: str = Field(default="")
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))


    document: "Document" = Relationship(back_populates="versions")
    creator: "User" = Relationship(back_populates="document_versions")


if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User