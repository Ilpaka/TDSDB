"""Операции над документами и их версиями."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.permissions import can_edit_project, can_view_project
from app.core.problems import APIProblem, Problems
from app.models.audit_log import EntityType
from app.models.document import Document, DocumentStatus
from app.models.document_version import DocumentVersion
from app.models.project import Project
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.schemas.document_version import DocumentVersionReadWithCreator

ALLOWED_STATUS_TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
    DocumentStatus.draft: {DocumentStatus.published, DocumentStatus.archived},
    DocumentStatus.published: {DocumentStatus.draft, DocumentStatus.archived},
    DocumentStatus.archived: {DocumentStatus.draft},
}
"""Допустимые переходы состояния документа.

Публикация архивированного документа запрещена: документ сначала
возвращается в состояние черновика.
"""


class DocumentService:
    """Создание, чтение, изменение, удаление документов и работа с версиями."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, document_id: int) -> Optional[Document]:
        """Вернуть документ по идентификатору."""
        return self.session.get(Document, document_id)

    def _require_project(self, project_id: int) -> Project:
        """Вернуть проект или сообщить о его отсутствии.

        Raises:
            APIProblem: Если проект не существует.
        """
        project = self.session.get(Project, project_id)
        if not project:
            raise APIProblem(
                Problems.PROJECT_NOT_FOUND,
                f"Project {project_id} does not exist or is unavailable",
            )
        return project

    def _require_document(self, document_id: int) -> Document:
        """Вернуть документ или сообщить о его отсутствии.

        Raises:
            APIProblem: Если документ не существует.
        """
        document = self.get_by_id(document_id)
        if not document:
            raise APIProblem(
                Problems.DOCUMENT_NOT_FOUND,
                f"Document {document_id} does not exist or is unavailable",
            )
        return document

    def _require_edit_permission(self, user: User, project_id: int) -> None:
        """Проверить право изменять документы проекта.

        Raises:
            APIProblem: Если у пользователя нет уровня доступа editor.
        """
        if not can_edit_project(self.session, user, project_id):
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Editor access to the project is required for this operation",
            )

    def _require_view_access(self, user: User, project_id: int, document_id: int) -> None:
        """Проверить право просматривать документы проекта.

        Документ недоступного проекта представляется как несуществующий:
        факт его наличия не раскрывается (правило STD-SEC-07).

        Raises:
            APIProblem: Если проект недоступен пользователю.
        """
        if not can_view_project(self.session, user, project_id):
            raise APIProblem(
                Problems.DOCUMENT_NOT_FOUND,
                f"Document {document_id} does not exist or is unavailable",
            )

    def _require_project_view_access(self, user: User, project_id: int) -> None:
        """Проверить право просматривать проект.

        Raises:
            APIProblem: Если проект недоступен пользователю.
        """
        if not can_view_project(self.session, user, project_id):
            raise APIProblem(
                Problems.PROJECT_NOT_FOUND,
                f"Project {project_id} does not exist or is unavailable",
            )

    def _next_version_number(self, document_id: int) -> int:
        """Вернуть номер следующей версии документа."""
        statement = select(func.max(DocumentVersion.version)).where(
            DocumentVersion.document_id == document_id
        )
        return (self.session.exec(statement).first() or 0) + 1

    def _add_version(self, document: Document, user: User) -> DocumentVersion:
        """Сохранить текущее содержимое документа как новую версию."""
        version = DocumentVersion(
            document_id=document.id,
            version=self._next_version_number(document.id),
            content_snapshot=document.content,
            created_by=user.id,
        )
        self.session.add(version)
        self.session.commit()
        return version

    def create_document(
        self, project_id: int, doc_data: DocumentCreate, user: User
    ) -> Document:
        """Создать документ в проекте.

        Args:
            project_id: Идентификатор проекта.
            doc_data: Название и содержимое документа.
            user: Пользователь, выполняющий операцию.

        Returns:
            Созданный документ с первой сохранённой версией.

        Raises:
            APIProblem: Если проект не найден либо у пользователя нет прав
                на изменение его документов.
        """
        self._require_project(project_id)
        self._require_edit_permission(user, project_id)

        document = Document(
            project_id=project_id,
            title=doc_data.title,
            content=doc_data.content or "",
            status=DocumentStatus.draft,
            created_by=user.id,
            updated_by=user.id,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)

        self._add_version(document, user)

        log_action(
            session=self.session,
            user_id=user.id,
            action="create_document",
            entity_type=EntityType.document,
            entity_id=document.id,
            meta={"title": document.title, "project_id": project_id},
        )

        return document

    def list_documents(
        self,
        project_id: int,
        user: User,
        offset: int = 0,
        limit: int = 20,
        document_status: Optional[DocumentStatus] = None,
    ) -> tuple[list[Document], int]:
        """Вернуть страницу документов проекта.

        Args:
            project_id: Идентификатор проекта.
            user: Пользователь, выполняющий запрос.
            offset: Смещение от начала коллекции.
            limit: Размер страницы.
            document_status: Отбор по состоянию документа.

        Returns:
            Документы текущей страницы и общее количество документов.

        Raises:
            APIProblem: Если проект не найден или недоступен пользователю.
        """
        self._require_project(project_id)
        self._require_project_view_access(user, project_id)

        conditions = [Document.project_id == project_id]
        if document_status:
            conditions.append(Document.status == document_status)

        total = self.session.exec(
            select(func.count()).select_from(Document).where(*conditions)
        ).one()

        statement = (
            select(Document).where(*conditions).order_by(Document.id).offset(offset).limit(limit)
        )

        return list(self.session.exec(statement).all()), total

    def get_document(self, document_id: int, user: User) -> Document:
        """Вернуть документ, доступный пользователю.

        Args:
            document_id: Идентификатор документа.
            user: Пользователь, выполняющий запрос.

        Returns:
            Карточка документа.

        Raises:
            APIProblem: Если документ не существует или недоступен.
        """
        document = self._require_document(document_id)
        self._require_view_access(user, document.project_id, document_id)
        return document

    def update_document(
        self, document_id: int, doc_data: DocumentUpdate, user: User
    ) -> Document:
        """Изменить документ, включая его состояние.

        Изменение содержимого приводит к созданию новой версии. Изменение
        состояния допускается только по разрешённым переходам.

        Args:
            document_id: Идентификатор документа.
            doc_data: Изменяемые атрибуты; неуказанные поля не изменяются.
            user: Пользователь, выполняющий операцию.

        Returns:
            Изменённый документ.

        Raises:
            APIProblem: Если документ не найден, у пользователя нет прав
                либо переход состояния недопустим.
        """
        document = self._require_document(document_id)
        self._require_edit_permission(user, document.project_id)

        update_data = doc_data.model_dump(exclude_unset=True)
        new_status = update_data.get("status")

        if new_status and new_status != document.status:
            if new_status not in ALLOWED_STATUS_TRANSITIONS[document.status]:
                raise APIProblem(
                    Problems.INVALID_STATE_TRANSITION,
                    f"Document cannot be moved from {document.status.value} "
                    f"to {new_status.value}",
                )

        content_changed = (
            "content" in update_data and update_data["content"] != document.content
        )

        for key, value in update_data.items():
            setattr(document, key, value)

        document.updated_by = user.id
        document.updated_at = datetime.now(timezone.utc)

        self.session.add(document)
        self.session.commit()

        if content_changed:
            self._add_version(document, user)

        self.session.refresh(document)

        log_action(
            session=self.session,
            user_id=user.id,
            action="update_document",
            entity_type=EntityType.document,
            entity_id=document_id,
            meta={
                "updated_fields": list(update_data.keys()),
                "content_changed": content_changed,
            },
        )

        return document

    def delete_document(self, document_id: int, user: User) -> None:
        """Удалить документ вместе с его версиями.

        Args:
            document_id: Идентификатор документа.
            user: Пользователь, выполняющий операцию.

        Raises:
            APIProblem: Если документ не найден либо у пользователя нет прав.
        """
        document = self._require_document(document_id)
        self._require_edit_permission(user, document.project_id)

        versions = self.session.exec(
            select(DocumentVersion).where(DocumentVersion.document_id == document_id)
        ).all()
        for version in versions:
            self.session.delete(version)

        project_id = document.project_id
        self.session.delete(document)
        self.session.commit()

        log_action(
            session=self.session,
            user_id=user.id,
            action="delete_document",
            entity_type=EntityType.document,
            entity_id=document_id,
            meta={"project_id": project_id},
        )

    def list_versions(
        self, document_id: int, user: User, offset: int = 0, limit: int = 20
    ) -> tuple[list[DocumentVersionReadWithCreator], int]:
        """Вернуть страницу версий документа.

        Args:
            document_id: Идентификатор документа.
            user: Пользователь, выполняющий запрос.
            offset: Смещение от начала коллекции.
            limit: Размер страницы.

        Returns:
            Версии текущей страницы в порядке убывания номера и общее
            количество версий.

        Raises:
            APIProblem: Если документ не существует или недоступен.
        """
        document = self._require_document(document_id)
        self._require_view_access(user, document.project_id, document_id)

        total = self.session.exec(
            select(func.count())
            .select_from(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
        ).one()

        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version.desc())
            .offset(offset)
            .limit(limit)
        )
        versions = self.session.exec(statement).all()

        items = []
        for version in versions:
            creator = self.session.get(User, version.created_by)
            items.append(
                DocumentVersionReadWithCreator(
                    id=version.id,
                    document_id=version.document_id,
                    version=version.version,
                    content_snapshot=version.content_snapshot,
                    created_by=version.created_by,
                    created_at=version.created_at,
                    creator_email=creator.email if creator else None,
                )
            )

        return items, total

    def get_version(self, document_id: int, version: int, user: User) -> DocumentVersion:
        """Вернуть конкретную версию документа.

        Args:
            document_id: Идентификатор документа.
            version: Номер версии.
            user: Пользователь, выполняющий запрос.

        Returns:
            Запрошенная версия документа.

        Raises:
            APIProblem: Если документ или версия не найдены либо документ
                недоступен пользователю.
        """
        document = self._require_document(document_id)
        self._require_view_access(user, document.project_id, document_id)

        return self._require_version(document_id, version)

    def _require_version(self, document_id: int, version: int) -> DocumentVersion:
        """Вернуть версию документа или сообщить о её отсутствии.

        Raises:
            APIProblem: Если версия не существует.
        """
        statement = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version == version,
        )
        stored = self.session.exec(statement).first()

        if not stored:
            raise APIProblem(
                Problems.VERSION_NOT_FOUND,
                f"Version {version} of document {document_id} does not exist",
            )

        return stored

    def restore_version(self, document_id: int, version: int, user: User) -> Document:
        """Восстановить содержимое документа из указанной версии.

        Восстановление не изменяет историю: текущее содержимое заменяется
        снимком выбранной версии и сохраняется как новая версия.

        Args:
            document_id: Идентификатор документа.
            version: Номер восстанавливаемой версии.
            user: Пользователь, выполняющий операцию.

        Returns:
            Документ с восстановленным содержимым.

        Raises:
            APIProblem: Если документ или версия не найдены либо
                у пользователя нет прав на изменение.
        """
        document = self._require_document(document_id)
        self._require_edit_permission(user, document.project_id)

        stored = self._require_version(document_id, version)

        document.content = stored.content_snapshot
        document.updated_by = user.id
        document.updated_at = datetime.now(timezone.utc)

        self.session.add(document)
        self.session.commit()

        created = self._add_version(document, user)
        self.session.refresh(document)

        log_action(
            session=self.session,
            user_id=user.id,
            action="restore_version",
            entity_type=EntityType.document,
            entity_id=document_id,
            meta={"restored_version": version, "new_version": created.version},
        )

        return document
