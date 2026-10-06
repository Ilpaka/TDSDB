"""Управление доступом участников к проектам."""

from typing import Optional

from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.permissions import can_manage_project
from app.core.problems import APIProblem, Problems
from app.models.audit_log import EntityType
from app.models.project import Project
from app.models.project_access import Permission, ProjectAccess
from app.models.user import User
from app.schemas.project_access import ProjectAccessReadWithUser


class AccessService:
    """Операции над правами доступа к проектам."""

    def __init__(self, session: Session):
        self.session = session

    
    def _check_project_exists(self, project_id: int) -> Project:
        """Вернуть проект или сообщить о его отсутствии."""
        project = self.session.get(Project, project_id)
        if not project:
            raise APIProblem(
                Problems.PROJECT_NOT_FOUND,
                f"Project {project_id} does not exist or is unavailable",
            )
        return project

    def _check_user_exists(self, user_id: int) -> User:
        """Вернуть участника или сообщить о его отсутствии."""
        user = self.session.get(User, user_id)
        if not user:
            raise APIProblem(
                Problems.USER_NOT_FOUND,
                f"User {user_id} does not exist",
            )
        return user

    def _check_manage_permission(self, user: User, project_id: int) -> None:
        """Проверить право управлять доступом к проекту."""
        if not can_manage_project(self.session, user, project_id):
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Only the project owner or an administrator can manage project access",
            )

    def get_access(self, project_id: int, user_id: int) -> Optional[ProjectAccess]:
        """Вернуть запись о доступе участника к проекту."""
        statement = select(ProjectAccess).where(
            ProjectAccess.project_id == project_id,
            ProjectAccess.user_id == user_id
        )
        return self.session.exec(statement).first()
        
    def upsert_access(
        self,
        project_id: int,
        user_id: int,
        permission: Permission,
        granted_by: User,
    ) -> tuple[ProjectAccessReadWithUser, bool]:
        """Выдать участнику доступ к проекту или изменить существующий.

        Args:
            project_id: Идентификатор проекта.
            user_id: Идентификатор участника.
            permission: Назначаемый уровень доступа.
            granted_by: Пользователь, выполняющий операцию.

        Returns:
            Запись о доступе и признак того, что запись была создана.

        Raises:
            APIProblem: Если проект или участник не найдены либо у
                пользователя нет права управлять доступом.
        """
        self._check_project_exists(project_id)
        self._check_manage_permission(granted_by, project_id)
        target_user = self._check_user_exists(user_id)

        existing_access = self.get_access(project_id, user_id)
        created = existing_access is None

        if existing_access:
            existing_access.permission = permission
            existing_access.granted_by = granted_by.id
            self.session.add(existing_access)
            self.session.commit()
            self.session.refresh(existing_access)
            access = existing_access
            action = "update_access"

        else:
            # Create new access
            access = ProjectAccess(
                project_id=project_id,
                user_id=user_id,
                permission=permission,
                granted_by=granted_by.id,
            )
            self.session.add(access)
            self.session.commit()
            self.session.refresh(access)
            action = "grant_access"

        log_action(
            session=self.session,
            user_id=granted_by.id,
            action=action,
            entity_type=EntityType.access,
            entity_id=access.id,
            meta={
                "project_id": project_id,
                "target_user_id": user_id,
                "permission": permission.value,
            },
        )

        payload = ProjectAccessReadWithUser(
            id=access.id,
            project_id=access.project_id,
            user_id=access.user_id,
            permission=access.permission,
            granted_by=access.granted_by,
            created_at=access.created_at,
            user_email=target_user.email,
            granter_email=granted_by.email,
        )

        return payload, created

    def revoke_access(self, project_id: int, user_id: int, revoked_by: User) -> None:
        """Отозвать доступ участника к проекту.

        Args:
            project_id: Идентификатор проекта.
            user_id: Идентификатор участника.
            revoked_by: Пользователь, выполняющий операцию.

        Raises:
            APIProblem: Если проект или запись о доступе не найдены либо у
                пользователя нет права управлять доступом.
        """
        self._check_project_exists(project_id)
        self._check_manage_permission(revoked_by, project_id)
        
        access = self.get_access(project_id, user_id)
        if not access:
            raise APIProblem(
                Problems.USER_NOT_FOUND,
                f"User {user_id} has no access to project {project_id}",
            )
        
        access_id = access.id
        self.session.delete(access)
        self.session.commit()

        log_action(
            session=self.session,
            user_id=revoked_by.id,
            action="revoke_access",
            entity_type=EntityType.access,
            entity_id=access_id,
            meta={
                "project_id": project_id,
                "target_user_id": user_id
            }
        )

    def list_project_access(
        self,
        project_id: int,
        user: User,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ProjectAccessReadWithUser], int]:
        """Вернуть страницу записей о доступе к проекту.

        Args:
            project_id: Идентификатор проекта.
            user: Пользователь, выполняющий запрос.
            offset: Смещение от начала коллекции.
            limit: Размер страницы.

        Returns:
            Записи текущей страницы и общее количество записей.

        Raises:
            APIProblem: Если проект не найден либо у пользователя нет права
                управлять доступом.
        """
        self._check_project_exists(project_id)
        self._check_manage_permission(user, project_id)

        total = self.session.exec(
            select(func.count())
            .select_from(ProjectAccess)
            .where(ProjectAccess.project_id == project_id)
        ).one()

        statement = (
            select(ProjectAccess)
            .where(ProjectAccess.project_id == project_id)
            .order_by(ProjectAccess.id)
            .offset(offset)
            .limit(limit)
        )
        accesses = self.session.exec(statement).all()

        result = []
        for access in accesses:
            target_user = self.session.get(User, access.user_id)
            granter = self.session.get(User, access.granted_by)
            result.append(ProjectAccessReadWithUser(
                id=access.id,
                project_id=access.project_id,
                user_id=access.user_id,
                permission=access.permission,
                granted_by=access.granted_by,
                created_at=access.created_at,
                user_email=target_user.email if target_user else None,
                granter_email=granter.email if granter else None,
            ))

        return result, total

    
