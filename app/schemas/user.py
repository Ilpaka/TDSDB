"""Схемы пользователей публичного API."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import APISchema

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
"""Пароль содержит не менее восьми символов, букву и цифру."""


class UserBase(BaseModel):
    """Общие поля пользователя."""

    email: EmailStr = Field(description="Адрес электронной почты", examples=["user@example.com"])


class UserCreate(UserBase):
    """Данные для создания учётной записи."""

    password: str = Field(
        min_length=8,
        description="Пароль: не менее 8 символов, содержит букву и цифру",
        examples=["Passw0rd123"],
    )
    role: UserRole = Field(default=UserRole.viewer, description="Назначаемая роль")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Проверить сложность пароля.

        Args:
            value: Пароль в открытом виде.

        Returns:
            Исходный пароль, если он удовлетворяет требованиям.

        Raises:
            ValueError: Если пароль не содержит буквы и цифры.
        """
        if not PASSWORD_PATTERN.fullmatch(value):
            raise ValueError("Password must contain at least one letter and one digit")
        return value


class UserUpdate(BaseModel):
    """Изменяемые атрибуты учётной записи."""

    role: Optional[UserRole] = Field(default=None, description="Новая роль пользователя")
    is_active: Optional[bool] = Field(
        default=None, description="Признак активности учётной записи"
    )


class UserLogin(UserBase):
    """Учётные данные для входа."""

    password: str = Field(description="Пароль в открытом виде", examples=["Passw0rd123"])


class UserRead(APISchema):
    """Карточка пользователя.

    Хэш пароля и иные внутренние атрибуты в контракт не входят.
    """

    id: int = Field(description="Идентификатор пользователя")
    email: EmailStr = Field(description="Адрес электронной почты")
    role: UserRole = Field(description="Роль пользователя")
    is_active: bool = Field(description="Признак активности учётной записи")
    created_at: datetime = Field(description="Момент создания учётной записи")
