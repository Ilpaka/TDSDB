"""ORM-модели хранилища.

Импорт пакета регистрирует все таблицы в метаданных SQLModel, поэтому
создание схемы и разрешение связей не зависят от порядка импорта роутеров.
"""

from app.models.audit_log import AuditLog, EntityType
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.models.project_access import Permission, ProjectAccess
from app.models.user import User, UserRole

__all__ = [
    "AuditLog",
    "Document",
    "DocumentStatus",
    "DocumentVersion",
    "EntityType",
    "Permission",
    "Project",
    "ProjectAccess",
    "User",
    "UserRole",
]
