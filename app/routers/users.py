"""Операции над учётными записями пользователей."""

from typing import Optional

from fastapi import APIRouter, Path, Query, status

from app.core.deps import AdminUser, Pagination, SessionDep
from app.core.problems import Problems, problem_responses
from app.models.user import UserRole
from app.schemas.pagination import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=Page[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Получить список пользователей",
    response_description="Страница учётных записей",
    operation_id="list_users",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.VALIDATION_ERROR,
    ),
)
def list_users(
    session: SessionDep,
    current_user: AdminUser,
    pagination: Pagination,
    role: Optional[UserRole] = Query(default=None, description="Отбор по роли пользователя"),
) -> Page[UserRead]:
    """Вернуть учётные записи пользователей.

    Операция доступна только администратору.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный администратор.
        pagination: Параметры постраничного обхода.
        role: Отбор по роли пользователя.

    Returns:
        Страница учётных записей с метаданными пагинации.
    """
    service = UserService(session)
    items, total = service.list_users(pagination.offset, pagination.limit, role)
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    response_description="Созданная учётная запись",
    operation_id="create_user",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.EMAIL_ALREADY_EXISTS,
        Problems.VALIDATION_ERROR,
    ),
)
def create_user(
    session: SessionDep,
    current_user: AdminUser,
    user_data: UserCreate,
) -> UserRead:
    """Создать учётную запись пользователя.

    Операция доступна только администратору. Самостоятельная регистрация
    в системе не предусмотрена.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный администратор.
        user_data: Адрес, пароль и роль новой учётной записи.

    Returns:
        Созданная учётная запись.
    """
    service = UserService(session)
    return service.create_user(user_data, current_user)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Изменить пользователя",
    response_description="Изменённая учётная запись",
    operation_id="update_user",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.USER_NOT_FOUND,
        Problems.VALIDATION_ERROR,
    ),
)
def update_user(
    session: SessionDep,
    current_user: AdminUser,
    user_data: UserUpdate,
    user_id: int = Path(description="Идентификатор пользователя", ge=1),
) -> UserRead:
    """Изменить роль или состояние учётной записи.

    Неуказанные поля не изменяются. Администратор не может деактивировать
    собственную учётную запись.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный администратор.
        user_data: Изменяемые атрибуты учётной записи.
        user_id: Идентификатор изменяемой учётной записи.

    Returns:
        Изменённая учётная запись.
    """
    service = UserService(session)
    return service.update_user(user_id, user_data, current_user)
