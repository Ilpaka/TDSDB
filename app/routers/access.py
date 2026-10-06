"""Операции управления доступом участников к проектам."""

from fastapi import APIRouter, Path, Response, status

from app.core.deps import CurrentUser, Pagination, SessionDep
from app.core.problems import Problems, problem_responses
from app.schemas.pagination import Page
from app.schemas.project_access import ProjectAccessReadWithUser, ProjectAccessUpsert
from app.services.access_service import AccessService

router = APIRouter(prefix="/projects/{project_id}/access", tags=["Access"])


@router.get(
    "",
    response_model=Page[ProjectAccessReadWithUser],
    status_code=status.HTTP_200_OK,
    summary="Получить список доступов проекта",
    response_description="Страница записей о выданных доступах",
    operation_id="list_project_access",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def list_project_access(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Pagination,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
) -> Page[ProjectAccessReadWithUser]:
    """Вернуть участников проекта и выданные им уровни доступа.

    Операция доступна владельцу проекта и администратору.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        pagination: Параметры постраничного обхода.
        project_id: Идентификатор проекта.

    Returns:
        Страница записей о доступе с метаданными пагинации.
    """
    service = AccessService(session)
    items, total = service.list_project_access(
        project_id, current_user, pagination.offset, pagination.limit
    )
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.put(
    "/{user_id}",
    response_model=ProjectAccessReadWithUser,
    status_code=status.HTTP_200_OK,
    summary="Выдать или изменить доступ участника",
    response_description="Запись о доступе участника к проекту",
    operation_id="upsert_project_access",
    responses={
        status.HTTP_201_CREATED: {
            "model": ProjectAccessReadWithUser,
            "description": "Доступ выдан впервые",
        },
        **problem_responses(
            Problems.AUTHENTICATION_REQUIRED,
            Problems.ACCESS_DENIED,
            Problems.PROJECT_NOT_FOUND,
            Problems.VALIDATION_ERROR,
        ),
    },
)
def upsert_project_access(
    session: SessionDep,
    current_user: CurrentUser,
    access_data: ProjectAccessUpsert,
    response: Response,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
    user_id: int = Path(description="Идентификатор участника", ge=1),
) -> ProjectAccessReadWithUser:
    """Назначить участнику уровень доступа к проекту.

    Операция идемпотентна: повторный вызов с тем же телом не изменяет
    состояние. Код 201 возвращается, если доступ выдан впервые, код 200 —
    если изменён существующий уровень доступа.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        access_data: Назначаемый уровень доступа.
        response: Ответ, код которого уточняется по результату операции.
        project_id: Идентификатор проекта.
        user_id: Идентификатор участника.

    Returns:
        Актуальная запись о доступе участника.
    """
    service = AccessService(session)
    access, created = service.upsert_access(
        project_id, user_id, access_data.permission, current_user
    )

    if created:
        response.status_code = status.HTTP_201_CREATED

    return access


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отозвать доступ участника",
    response_description="Доступ отозван",
    operation_id="revoke_project_access",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.PROJECT_NOT_FOUND,
        Problems.USER_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def revoke_project_access(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
    user_id: int = Path(description="Идентификатор участника", ge=1),
) -> None:
    """Отозвать ранее выданный доступ участника к проекту.

    \f

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        project_id: Идентификатор проекта.
        user_id: Идентификатор участника.
    """
    service = AccessService(session)
    service.revoke_access(project_id, user_id, current_user)
