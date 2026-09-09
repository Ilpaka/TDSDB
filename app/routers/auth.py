"""Операции аутентификации."""

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, SessionDep
from app.core.problems import Problems, problem_responses
from app.schemas.token import Token
from app.schemas.user import UserLogin, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Выполнить вход",
    response_description="Токен доступа со схемой Bearer",
    operation_id="login",
    responses=problem_responses(
        Problems.INVALID_CREDENTIALS,
        Problems.USER_DEACTIVATED,
        Problems.VALIDATION_ERROR,
    ),
)
def login(session: SessionDep, credentials: UserLogin) -> Token:
    """Проверить учётные данные и выпустить токен доступа.

    Операция доступна без аутентификации. Полученный токен передаётся
    в заголовке ``Authorization: Bearer <token>``.

    Args:
        session: Сессия базы данных.
        credentials: Адрес и пароль пользователя.

    Returns:
        Токен доступа и его тип.
    """
    service = UserService(session)
    return service.authenticate(credentials)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получить текущего пользователя",
    response_description="Карточка аутентифицированного пользователя",
    operation_id="get_current_user",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.USER_DEACTIVATED,
    ),
)
def get_me(current_user: CurrentUser) -> UserRead:
    """Вернуть карточку пользователя, которому принадлежит токен.

    Args:
        current_user: Аутентифицированный пользователь.

    Returns:
        Карточка текущего пользователя.
    """
    return current_user
