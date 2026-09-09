"""Схемы версий документов."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import APISchema


class DocumentVersionRestore(BaseModel):
    """Запрос на создание версии из ранее сохранённой."""

    restore_from: int = Field(
        ge=1,
        description="Номер версии, содержимое которой восстанавливается",
        examples=[2],
    )


class DocumentVersionRead(APISchema):
    """Сохранённая версия документа."""

    id: int = Field(description="Идентификатор версии")
    document_id: int = Field(description="Идентификатор документа")
    version: int = Field(description="Порядковый номер версии")
    content_snapshot: str = Field(description="Содержимое документа на момент сохранения")
    created_by: int = Field(description="Идентификатор пользователя, создавшего версию")
    created_at: datetime = Field(description="Момент создания версии")


class DocumentVersionReadWithCreator(DocumentVersionRead):
    """Версия документа с адресом создавшего её пользователя."""

    creator_email: Optional[str] = Field(
        default=None, description="Адрес пользователя, создавшего версию"
    )
