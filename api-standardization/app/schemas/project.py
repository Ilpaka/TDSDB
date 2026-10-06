"""Схемы проектов публичного API."""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import APISchema, UTCDateTime


class ProjectBase(BaseModel):
    """Общие поля проекта."""

    title: str = Field(
        min_length=3,
        max_length=120,
        description="Название проекта, от 3 до 120 символов",
        examples=["Реконструкция котельной"],
    )
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Описание проекта"
    )


class ProjectCreate(ProjectBase):
    """Данные для создания проекта."""


class ProjectUpdate(BaseModel):
    """Изменяемые атрибуты проекта; неуказанные поля не изменяются.

    Обязательные атрибуты ресурса можно не передавать, но явный ``null``
    для них отклоняется кодом 422 (STD-DATA-08); ``null`` допускается только
    для необязательных полей и означает очистку значения.
    """

    title: str = Field(
        default=None, min_length=3, max_length=120, description="Новое название проекта"
    )
    description: Optional[str] = Field(
        default=None, max_length=2000, description="Новое описание проекта"
    )


class ProjectRead(APISchema):
    """Карточка проекта."""

    id: int = Field(description="Идентификатор проекта")
    title: str = Field(description="Название проекта")
    description: Optional[str] = Field(default=None, description="Описание проекта")
    owner_id: int = Field(description="Идентификатор владельца проекта")
    created_at: UTCDateTime = Field(description="Момент создания проекта")


class ProjectReadWithOwner(ProjectRead):
    """Карточка проекта с адресом владельца."""

    owner_email: Optional[str] = Field(default=None, description="Адрес владельца проекта")
