"""Операции над проектами."""

from typing import Optional

from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.problems import APIProblem, Problems
from app.core.permissions import can_manage_project, can_view_project
from app.models.audit_log import EntityType
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.models.project_access import ProjectAccess
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    """Создание, чтение, изменение и удаление проектов."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Вернуть проект по идентификатору."""
        return self.session.get(Project, project_id)

    def _require_project(self, project_id: int) -> Project:
        """Вернуть проект или сообщить о его отсутствии.

        Raises:
            APIProblem: Если проект не существует.
        """
        project = self.get_by_id(project_id)
        if not project:
            raise APIProblem(
                Problems.PROJECT_NOT_FOUND,
                f"Project {project_id} does not exist or is unavailable",
            )
        return project

    def _require_manage_permission(self, user: User, project_id: int) -> None:
        """Проверить право изменять проект.

        Raises:
            APIProblem: Если пользователь не владелец и не администратор.
        """
        if not can_manage_project(self.session, user, project_id):
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Only the project owner or an administrator can modify this project",
            )

    def _accessible_project_ids(self, user: User) -> set[int]:
        """Вернуть идентификаторы проектов, доступных пользователю."""
        owned = self.session.exec(
            select(Project.id).where(Project.owner_id == user.id)
        ).all()
        granted = self.session.exec(
            select(ProjectAccess.project_id).where(ProjectAccess.user_id == user.id)
        ).all()
        return set(owned) | set(granted)

    def create_project(self, project_data: ProjectCreate, owner: User) -> Project:
        """Создать проект.

        Args:
            project_data: Название и описание проекта.
            owner: Пользователь, становящийся владельцем проекта.

        Returns:
            Созданный проект.
        """
        
        project = Project(
            title=project_data.title,
            description=project_data.description,
            owner_id=owner.id
        )
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)

        log_action(
            session=self.session,
            user_id=owner.id,
            action="create_project",
            entity_type=EntityType.project,
            entity_id=project.id,
            meta={"title": project.title}
        )
        
        return project
    

    def list_projects(
        self, user: User, offset: int = 0, limit: int = 20
    ) -> tuple[list[Project], int]:
        """Вернуть страницу проектов, доступных пользователю.

        Администратор получает все проекты, остальные роли — проекты,
        которыми владеют, и проекты с выданным доступом.

        Args:
            user: Пользователь, выполняющий запрос.
            offset: Смещение от начала коллекции.
            limit: Размер страницы.

        Returns:
            Проекты текущей страницы и общее количество доступных проектов.
        """
        if user.role == UserRole.admin:
            conditions = []
        else:
            accessible = self._accessible_project_ids(user)
            if not accessible:
                return [], 0
            conditions = [Project.id.in_(accessible)]

        total = self.session.exec(
            select(func.count()).select_from(Project).where(*conditions)
        ).one()

        statement = (
            select(Project).where(*conditions).order_by(Project.id).offset(offset).limit(limit)
        )

        return list(self.session.exec(statement).all()), total

    def get_project(self, project_id: int, user: User) -> Project:
        """Вернуть проект, доступный пользователю.

        Проект, недоступный пользователю, представляется как несуществующий:
        факт наличия чужого проекта не раскрывается (правило STD-SEC-07).

        Args:
            project_id: Идентификатор проекта.
            user: Пользователь, выполняющий запрос.

        Returns:
            Проект, доступный пользователю.

        Raises:
            APIProblem: Если проект не существует или недоступен.
        """
        project = self._require_project(project_id)

        if not can_view_project(self.session, user, project_id):
            raise APIProblem(
                Problems.PROJECT_NOT_FOUND,
                f"Project {project_id} does not exist or is unavailable",
            )

        return project

    def update_project(
        self, project_id: int, project_data: ProjectUpdate, user: User
    ) -> Project:
        """Изменить атрибуты проекта.

        Args:
            project_id: Идентификатор проекта.
            project_data: Изменяемые атрибуты; неуказанные поля не изменяются.
            user: Пользователь, выполняющий операцию.

        Returns:
            Изменённый проект.

        Raises:
            APIProblem: Если проект не найден либо у пользователя нет прав.
        """
        project = self._require_project(project_id)
        self._require_manage_permission(user, project_id)
        
        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)

        log_action(
            session=self.session,
            user_id=user.id,
            action="update_project",
            entity_type=EntityType.project,
            entity_id=project.id,
            meta={"updated_fields": list(update_data.keys())}
        )
        
        return project
    
    def _delete_dependent_records(self, project_id: int) -> None:
        """Удалить записи, ссылающиеся на проект.

        Версии документов, документы и выданные доступы удаляются до
        удаления самого проекта: внешние ключи объявлены обязательными,
        поэтому их обнуление недопустимо.

        Args:
            project_id: Идентификатор проекта.
        """
        document_ids = self.session.exec(
            select(Document.id).where(Document.project_id == project_id)
        ).all()

        if document_ids:
            versions = self.session.exec(
                select(DocumentVersion).where(DocumentVersion.document_id.in_(document_ids))
            ).all()
            for version in versions:
                self.session.delete(version)

            documents = self.session.exec(
                select(Document).where(Document.project_id == project_id)
            ).all()
            for document in documents:
                self.session.delete(document)

        accesses = self.session.exec(
            select(ProjectAccess).where(ProjectAccess.project_id == project_id)
        ).all()
        for access in accesses:
            self.session.delete(access)

        self.session.flush()

    def delete_project(self, project_id: int, user: User) -> None:
        """Удалить проект.

        Args:
            project_id: Идентификатор проекта.
            user: Пользователь, выполняющий операцию.

        Raises:
            APIProblem: Если проект не найден либо у пользователя нет прав.
        """
        project = self._require_project(project_id)
        self._require_manage_permission(user, project_id)
        
        project_title = project.title
        self._delete_dependent_records(project_id)
        self.session.delete(project)
        self.session.commit()

        log_action(
            session=self.session,
            user_id=user.id,
            action="delete_project",
            entity_type=EntityType.project,
            entity_id=project_id,
            meta={"title": project_title}
        )


    
        
