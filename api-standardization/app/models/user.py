"""Модель учётной записи пользователя."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from enum import Enum 


from sqlmodel import SQLModel, Field, Relationship


class UserRole(str, Enum):
    """Роль пользователя: admin, manager, worker или viewer."""

    admin = "admin"
    manager = "manager"
    worker = "worker"
    viewer = "viewer"


class User(SQLModel, table=True):
    """Учётная запись пользователя.

    Хэш пароля хранится только в модели хранилища и не входит в схемы ответа.
    """

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.viewer)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))

    owner_projects: list["Project"] = Relationship(back_populates="owner")

    project_accesses: list["ProjectAccess"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "ProjectAccess.user_id"}
    )

    granted_access: list["ProjectAccess"] = Relationship(
        back_populates="granter",
        sa_relationship_kwargs={"foreign_keys": "ProjectAccess.granted_by"}
    )

    created_documents: list["Document"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "Document.created_by"}
    )
    updated_documents: list["Document"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "Document.updated_by"}
    )

    document_versions: list["DocumentVersion"] = Relationship(
        back_populates="creator"
    )

    audit_logs: list["AuditLog"] = Relationship(back_populates="user")


if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.project_access import ProjectAccess
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.audit_log import AuditLog

