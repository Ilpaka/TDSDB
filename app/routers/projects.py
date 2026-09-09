"""Операции над проектами."""

from fastapi import APIRouter, Path, status

from app.core.deps import CurrentUser, Pagination, ProjectManagerUser, SessionDep
from app.core.problems import Problems, problem_responses
from app.schemas.pagination import Page
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=Page[ProjectRead],
    status_code=status.HTTP_200_OK,
    summary="Получить список проектов",
    response_description="Страница проектов, доступных пользователю",
    operation_id="list_projects",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.VALIDATION_ERROR,
    ),
)
def list_projects(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Pagination,
) -> Page[ProjectRead]:
    """Вернуть проекты, доступные текущему пользователю.

    Администратор получает все проекты. Остальные роли — проекты,
    которыми владеют, и проекты с выданным доступом.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        pagination: Параметры постраничного обхода.

    Returns:
        Страница проектов с метаданными пагинации.
    """
    service = ProjectService(session)
    items, total = service.list_projects(current_user, pagination.offset, pagination.limit)
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать проект",
    response_description="Созданный проект",
    operation_id="create_project",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.VALIDATION_ERROR,
    ),
)
def create_project(
    session: SessionDep,
    current_user: ProjectManagerUser,
    project_data: ProjectCreate,
) -> ProjectRead:
    """Создать проект и назначить текущего пользователя его владельцем.

    Операция доступна ролям admin и manager.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        project_data: Название и описание проекта.

    Returns:
        Созданный проект.
    """
    service = ProjectService(session)
    return service.create_project(project_data, current_user)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Получить проект",
    response_description="Карточка проекта",
    operation_id="get_project",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def get_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
) -> ProjectRead:
    """Вернуть проект, доступный текущему пользователю.

    Недоступный проект представляется как несуществующий: факт наличия
    чужого проекта не раскрывается.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        project_id: Идентификатор проекта.

    Returns:
        Карточка проекта.
    """
    service = ProjectService(session)
    return service.get_project(project_id, current_user)


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    status_code=status.HTTP_200_OK,
    summary="Изменить проект",
    response_description="Изменённый проект",
    operation_id="update_project",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def update_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_data: ProjectUpdate,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
) -> ProjectRead:
    """Изменить название или описание проекта.

    Операция доступна владельцу проекта и администратору. Неуказанные
    поля не изменяются.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        project_data: Изменяемые атрибуты проекта.
        project_id: Идентификатор проекта.

    Returns:
        Изменённый проект.
    """
    service = ProjectService(session)
    return service.update_project(project_id, project_data, current_user)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проект",
    response_description="Проект удалён",
    operation_id="delete_project",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.PROJECT_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def delete_project(
    session: SessionDep,
    current_user: CurrentUser,
    project_id: int = Path(description="Идентификатор проекта", ge=1),
) -> None:
    """Удалить проект вместе с зависимыми записями.

    Операция доступна владельцу проекта и администратору.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный пользователь.
        project_id: Идентификатор проекта.
    """
    service = ProjectService(session)
    service.delete_project(project_id, current_user)
