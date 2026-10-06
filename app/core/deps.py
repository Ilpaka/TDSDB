"""Общие зависимости FastAPI для роутеров публичного API.

Модуль собирает в одном месте типизированные зависимости, применяемые всеми
операциями: сессия базы данных, текущий пользователь, проверка роли и
параметры пагинации. Проверка роли реализована зависимостью, возбуждающей
ошибку доступа, согласно правилу STD-SEC-05 стандарта API_STANDARD.
"""

from typing import Annotated, Callable

from fastapi import Depends
from sqlmodel import Session

from app.core.problems import APIProblem, Problems
from app.core.security import get_current_user
from app.db.session import get_session
from app.models.user import User, UserRole
from app.schemas.pagination import PaginationParams, pagination_params

SessionDep = Annotated[Session, Depends(get_session)]
"""Сессия базы данных, управляемая системой зависимостей."""

CurrentUser = Annotated[User, Depends(get_current_user)]
"""Аутентифицированный пользователь текущего запроса."""

Pagination = Annotated[PaginationParams, Depends(pagination_params)]
"""Проверенные параметры постраничного обхода коллекции."""


def require_roles(*allowed_roles: UserRole) -> Callable[..., User]:
    """Создать зависимость, допускающую только перечисленные роли.

    Args:
        *allowed_roles: Роли, которым разрешена операция.

    Returns:
        Зависимость FastAPI, возвращающая текущего пользователя.

    Raises:
        APIProblem: Если роль пользователя не входит в перечень разрешённых.
    """

    def role_guard(current_user: CurrentUser) -> User:
        """Пропустить пользователя с разрешённой ролью либо вернуть 403."""
        if current_user.role not in allowed_roles:
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Operation requires one of the following roles: "
                + ", ".join(role.value for role in allowed_roles),
            )
        return current_user

    return role_guard


AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]
"""Пользователь с ролью администратора."""

ProjectManagerUser = Annotated[
    User, Depends(require_roles(UserRole.admin, UserRole.manager))
]
"""Пользователь, которому разрешено создавать проекты."""
