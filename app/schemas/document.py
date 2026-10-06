"""Схемы документов публичного API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.document import DocumentStatus
from app.schemas.base import APISchema

MAX_CONTENT_LENGTH = 100_000
"""Максимальная длина содержимого документа (OWASP API4)."""


class DocumentBase(BaseModel):
    """Общие поля документа."""

    title: str = Field(
        min_length=3,
        max_length=120,
        description="Название документа, от 3 до 120 символов",
        examples=["Пояснительная записка"],
    )
    content: Optional[str] = Field(
        default="",
        max_length=MAX_CONTENT_LENGTH,
        description=f"Содержимое документа, не более {MAX_CONTENT_LENGTH} символов",
        examples=["Раздел 1. Общие положения"],
    )


class DocumentCreate(DocumentBase):
    """Данные для создания документа."""


class DocumentUpdate(BaseModel):
    """Изменяемые атрибуты документа; неуказанные поля не изменяются."""

    title: Optional[str] = Field(
        default=None, min_length=3, max_length=120, description="Новое название документа"
    )
    content: Optional[str] = Field(
        default=None, max_length=MAX_CONTENT_LENGTH, description="Новое содержимое документа"
    )
    status: Optional[DocumentStatus] = Field(
        default=None,
        description=(
            "Новое состояние документа. Допустимые переходы: draft в published "
            "или archived, published в draft или archived, archived в draft"
        ),
        examples=["published"],
    )


class DocumentRead(APISchema):
    """Карточка документа."""

    id: int = Field(description="Идентификатор документа")
    project_id: int = Field(description="Идентификатор проекта")
    title: str = Field(description="Название документа")
    content: Optional[str] = Field(default=None, description="Содержимое документа")
    status: DocumentStatus = Field(description="Состояние документа")
    created_by: int = Field(description="Идентификатор автора")
    updated_by: Optional[int] = Field(
        default=None, description="Идентификатор пользователя, изменившего документ"
    )
    created_at: datetime = Field(description="Момент создания документа")
    updated_at: datetime = Field(description="Момент последнего изменения")


class DocumentReadWithDetails(DocumentRead):
    """Карточка документа с адресами участников и числом версий."""

    creator_email: Optional[str] = Field(default=None, description="Адрес автора")
    updater_email: Optional[str] = Field(
        default=None, description="Адрес пользователя, изменившего документ"
    )
    version_count: int = Field(default=0, description="Количество сохранённых версий")
