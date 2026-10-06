"""Операции над документами и их версиями."""

from typing import Optional

from fastapi import APIRouter, Path, Query, status

from app.core.deps import CurrentUser, Pagination, SessionDep
from app.core.problems import Problems, problem_responses
from app.models.document import DocumentStatus
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.schemas.document_version import (
    DocumentVersionRead,
    DocumentVersionReadWithCreator,
    DocumentVersionRestore,
)
from app.schemas.pagination import Page
from app.services.document_service import DocumentService

router = APIRouter(tags=["Documents"])


@router.get(
    "/projects/{project_id}/documents",
    response_model=Page[DocumentRead],
    status_code=status.HTTP_200_OK,
    summary="Получить документы проекта",
    response_description="Страница документов проекта",
    operation_id="list_project_documents",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def list_project_documents(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Pagination,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
    document_status: Optional[DocumentStatus] = Query(
        default=None, alias="status", description="Отбор по состоянию документа"
    ),
) -> Page[DocumentRead]:
    """Вернуть документы проекта, доступного пользователю.

    Требуется доступ к проекту уровня viewer или editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        pagination: Параметры постраничного обхода.
        project_id: Идентификатор проекта.
        document_status: Отбор по состоянию документа.

    Returns:
        Страница документов с метаданными пагинации.
    """
    service = DocumentService(session)
    items, total = service.list_documents(
        project_id,
        current_user,
        pagination.offset,
        pagination.limit,
        document_status,
    )
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать документ",
    response_description="Созданный документ",
    operation_id="create_document",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def create_document(
    session: SessionDep,
    current_user: CurrentUser,
    doc_data: DocumentCreate,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
) -> DocumentRead:
    """Создать документ в проекте.

    Документ создаётся в состоянии draft, его содержимое сохраняется
    как первая версия. Требуется уровень доступа editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        doc_data: Название и содержимое документа.
        project_id: Идентификатор проекта.

    Returns:
        Созданный документ.
    """
    service = DocumentService(session)
    return service.create_document(project_id, doc_data, current_user)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
    summary="Получить документ",
    response_description="Карточка документа",
    operation_id="get_document",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def get_document(
    session: SessionDep,
    current_user: CurrentUser,
    document_id: int = Path(description="Идентификатор документа", ge=1),
) -> DocumentRead:
    """Вернуть документ, доступный текущему пользователю.

    Документ недоступного проекта представляется как несуществующий.

    Требуется доступ к проекту уровня viewer или editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        document_id: Идентификатор документа.

    Returns:
        Карточка документа.
    """
    service = DocumentService(session)
    return service.get_document(document_id, current_user)


@router.patch(
    "/documents/{document_id}",
    response_model=DocumentRead,
    status_code=status.HTTP_200_OK,
    summary="Изменить документ",
    response_description="Изменённый документ",
    operation_id="update_document",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.INVALID_STATE_TRANSITION,
        Problems.VALIDATION_ERROR,
    ),
)
def update_document(
    session: SessionDep,
    current_user: CurrentUser,
    doc_data: DocumentUpdate,
    document_id: int = Path(description="Идентификатор документа", ge=1),
) -> DocumentRead:
    """Изменить название, содержимое или состояние документа.

    Публикация и архивирование выполняются изменением поля ``status``.
    Изменение содержимого создаёт новую версию. Требуется уровень
    доступа editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        doc_data: Изменяемые атрибуты документа.
        document_id: Идентификатор документа.

    Returns:
        Изменённый документ.
    """
    service = DocumentService(session)
    return service.update_document(document_id, doc_data, current_user)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить документ",
    response_description="Документ удалён",
    operation_id="delete_document",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def delete_document(
    session: SessionDep,
    current_user: CurrentUser,
    document_id: int = Path(description="Идентификатор документа", ge=1),
) -> None:
    """Удалить документ вместе со всеми его версиями.

    Требуется доступ к проекту уровня editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        document_id: Идентификатор документа.
    """
    service = DocumentService(session)
    service.delete_document(document_id, current_user)


@router.get(
    "/documents/{document_id}/versions",
    response_model=Page[DocumentVersionReadWithCreator],
    status_code=status.HTTP_200_OK,
    summary="Получить версии документа",
    response_description="Страница версий в порядке убывания номера",
    operation_id="list_document_versions",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def list_document_versions(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Pagination,
    document_id: int = Path(description="Идентификатор документа", ge=1),
) -> Page[DocumentVersionReadWithCreator]:
    """Вернуть сохранённые версии документа.

    Требуется доступ к проекту уровня viewer или editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        pagination: Параметры постраничного обхода.
        document_id: Идентификатор документа.

    Returns:
        Страница версий с метаданными пагинации.
    """
    service = DocumentService(session)
    items, total = service.list_versions(
        document_id, current_user, pagination.offset, pagination.limit
    )
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post(
    "/documents/{document_id}/versions",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Восстановить версию документа",
    response_description="Документ с восстановленным содержимым",
    operation_id="restore_document_version",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.VERSION_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def restore_document_version(
    session: SessionDep,
    current_user: CurrentUser,
    restore_data: DocumentVersionRestore,
    document_id: int = Path(description="Идентификатор документа", ge=1),
) -> DocumentRead:
    """Создать версию документа из ранее сохранённой.

    История версий не изменяется: содержимое выбранной версии становится
    текущим и сохраняется как новая версия. Требуется уровень доступа
    editor.

    Требуется доступ к проекту уровня editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        restore_data: Номер восстанавливаемой версии.
        document_id: Идентификатор документа.

    Returns:
        Документ с восстановленным содержимым.
    """
    service = DocumentService(session)
    return service.restore_version(document_id, restore_data.restore_from, current_user)


@router.get(
    "/documents/{document_id}/versions/{version}",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Получить версию документа",
    response_description="Сохранённая версия документа",
    operation_id="get_document_version",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.DOCUMENT_NOT_FOUND,
        Problems.VERSION_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def get_document_version(
    session: SessionDep,
    current_user: CurrentUser,
    document_id: int = Path(description="Идентификатор документа", ge=1),
    version: int = Path(description="Порядковый номер версии", ge=1),
) -> DocumentVersionRead:
    """Вернуть конкретную версию документа.

    Требуется доступ к проекту уровня viewer или editor.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        document_id: Идентификатор документа.
        version: Порядковый номер версии.

    Returns:
        Запрошенная версия документа.
    """
    service = DocumentService(session)
    return service.get_version(document_id, version, current_user)
