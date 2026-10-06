"""Чтение журнала действий пользователей."""

from datetime import date, datetime, time
from typing import Optional

from sqlmodel import Session, func, select

from app.models.audit_log import AuditLog, EntityType
from app.models.user import User
from app.schemas.audit_log import AuditLogReadWithUser


class AuditService:
    """Операции чтения журнала аудита."""

    def __init__(self, session: Session):
        self.session = session

    def list_logs(
        self,
        offset: int = 0,
        limit: int = 20,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
    ) -> tuple[list[AuditLogReadWithUser], int]:
        """Вернуть страницу записей журнала с учётом фильтров.

        Args:
            offset: Смещение от начала коллекции.
            limit: Размер страницы.
            date_from: Нижняя граница периода включительно.
            date_to: Верхняя граница периода включительно.
            user_id: Идентификатор пользователя, выполнившего действие.
            action: Точное наименование действия.
            entity_type: Тип сущности, к которой относится действие.

        Returns:
            Записи текущей страницы и общее количество записей,
            удовлетворяющих фильтрам.
        """
        conditions = []

        if date_from:
            conditions.append(AuditLog.created_at >= datetime.combine(date_from, time.min))

        if date_to:
            conditions.append(AuditLog.created_at <= datetime.combine(date_to, time.max))

        if user_id:
            conditions.append(AuditLog.user_id == user_id)

        if action:
            conditions.append(AuditLog.action == action)

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)

        total = self.session.exec(
            select(func.count()).select_from(AuditLog).where(*conditions)
        ).one()

        statement = (
            select(AuditLog)
            .where(*conditions)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        logs = self.session.exec(statement).all()

        items = []
        for log in logs:
            user = self.session.get(User, log.user_id)
            items.append(
                AuditLogReadWithUser(
                    id=log.id,
                    user_id=log.user_id,
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    meta=log.meta,
                    created_at=log.created_at,
                    user_email=user.email if user else None,
                )
            )

        return items, total
