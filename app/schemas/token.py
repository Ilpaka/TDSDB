"""Схемы токенов доступа."""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Токен доступа, выдаваемый при входе."""

    access_token: str = Field(
        description="Подписанный JWT; передаётся в заголовке Authorization",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxfQ.signature"],
    )
    token_type: str = Field(default="bearer", description="Схема токена", examples=["bearer"])


class TokenPayload(BaseModel):
    """Полезная нагрузка токена доступа."""

    user_id: int = Field(description="Идентификатор пользователя")
    role: str = Field(description="Роль пользователя на момент выпуска токена")
