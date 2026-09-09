"""Операции чтения журнала действий пользователей."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, status

from app.core.deps import AdminUser, Pagination, SessionDep
from app.core.problems import Problems, problem_responses
from app.models.audit_log import EntityType
from app.schemas.audit_log import AuditLogReadWithUser
from app.schemas.pagination import Page
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=Page[AuditLogReadWithUser],
    status_code=status.HTTP_200_OK,
    summary="Получить журнал действий",
    response_description="Страница записей журнала, отсортированная по убыванию времени",
    operation_id="list_audit_logs",
    responses=problem_responses(
        Problems.AUTHENTICATION_REQUIRED,
        Problems.ACCESS_DENIED,
        Problems.VALIDATION_ERROR,
    ),
)
def list_audit_logs(
    session: SessionDep,
    current_user: AdminUser,
    pagination: Pagination,
    date_from: Optional[date] = Query(
        default=None, description="Нижняя граница периода включительно"
    ),
    date_to: Optional[date] = Query(
        default=None, description="Верхняя граница периода включительно"
    ),
    user_id: Optional[int] = Query(
        default=None, ge=1, description="Идентификатор пользователя, выполнившего действие"
    ),
    action: Optional[str] = Query(
        default=None, min_length=1, max_length=100, description="Точное наименование действия"
    ),
    entity_type: Optional[EntityType] = Query(
        default=None, description="Тип сущности, к которой относится действие"
    ),
) -> Page[AuditLogReadWithUser]:
    """Вернуть записи журнала действий пользователей.

    Операция доступна только администратору.

    Args:
        session: Сессия базы данных.
        current_user: Аутентифицированный администратор.
        pagination: Параметры постраничного обхода.
        date_from: Нижняя граница периода включительно.
        date_to: Верхняя граница периода включительно.
        user_id: Идентификатор пользователя, выполнившего действие.
        action: Точное наименование действия.
        entity_type: Тип сущности, к которой относится действие.

    Returns:
        Страница записей журнала с метаданными пагинации.
    """
    service = AuditService(session)
    items, total = service.list_logs(
        offset=pagination.offset,
        limit=pagination.limit,
        date_from=date_from,
        date_to=date_to,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
    )
    return Page(
        items=items,
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )
