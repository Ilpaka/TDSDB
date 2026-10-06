"""Проверки доступа на уровне объекта (object-level authorization).

Функции модуля определяют уровень доступа пользователя к конкретному
проекту и применяются сервисным слоем до чтения или изменения данных
(правило STD-SEC-06 стандарта API_STANDARD, OWASP API1).

Порядок определения доступа:

1. администратор имеет уровень ``editor`` к любому проекту;
2. владелец проекта имеет уровень ``editor`` к своему проекту;
3. остальные пользователи имеют уровень, выданный записью ``ProjectAccess``;
4. при отсутствии записи доступ отсутствует.
"""

from typing import Optional

from sqlmodel import Session, select

from app.models.project import Project
from app.models.project_access import Permission, ProjectAccess
from app.models.user import User, UserRole


def get_user_project_permission(
    session: Session, user: User, project_id: int
) -> Optional[Permission]:
    """Определить уровень доступа пользователя к проекту.

    Args:
        session: Сессия базы данных.
        user: Аутентифицированный пользователь.
        project_id: Идентификатор проекта.

    Returns:
        Уровень доступа либо ``None``, если доступа нет.
    """
    if user.role == UserRole.admin:
        return Permission.editor

    project = session.get(Project, project_id)
    if project and project.owner_id == user.id:
        return Permission.editor

    statement = select(ProjectAccess).where(
        ProjectAccess.project_id == project_id,
        ProjectAccess.user_id == user.id,
    )
    access = session.exec(statement).first()

    return access.permission if access else None


def can_view_project(session: Session, user: User, project_id: int) -> bool:
    """Проверить право чтения проекта и его документов."""
    return get_user_project_permission(session, user, project_id) is not None


def is_project_owner_or_admin(session: Session, user: User, project_id: int) -> bool:
    """Проверить, является ли пользователь владельцем проекта или администратором."""
    if user.role == UserRole.admin:
        return True

    project = session.get(Project, project_id)
    return project is not None and project.owner_id == user.id


def can_manage_project(session: Session, user: User, project_id: int) -> bool:
    """Проверить право изменять проект и управлять доступом к нему."""
    return is_project_owner_or_admin(session, user, project_id)


def can_edit_project(session: Session, user: User, project_id: int) -> bool:
    """Проверить право создавать и изменять документы проекта."""
    return get_user_project_permission(session, user, project_id) == Permission.editor
