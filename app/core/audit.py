"""Запись действий пользователей в журнал аудита."""

import json
from typing import Any, Optional

from sqlmodel import Session

from app.models.audit_log import AuditLog, EntityType


def log_action(
    session: Session,
    user_id: int,
    action: str,
    entity_type: EntityType,
    entity_id: Optional[int] = None,
    meta: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """Сохранить запись о действии пользователя.

    Args:
        session: Сессия базы данных.
        user_id: Идентификатор пользователя, выполнившего действие.
        action: Наименование действия, например ``grant_access``.
        entity_type: Тип сущности, к которой относится действие.
        entity_id: Идентификатор сущности.
        meta: Дополнительные сведения; сохраняются в формате JSON.
            Пароли, токены и иные секреты в ``meta`` не передаются.

    Returns:
        Сохранённая запись журнала.
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=json.dumps(meta, ensure_ascii=False) if meta else None,
    )

    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log
