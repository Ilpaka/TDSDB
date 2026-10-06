"""Схемы ошибок публичного API.

Формат соответствует RFC 9457 Problem Details for HTTP APIs и правилам
STD-ERR-01…STD-ERR-09 стандарта API_STANDARD.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProblemDetails(BaseModel):
    """Тело ответа с ошибкой по RFC 9457."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "https://docs.local/problems/project-not-found",
                    "title": "Project not found",
                    "status": 404,
                    "detail": "Project 42 does not exist or is unavailable",
                    "instance": "/api/v1/projects/42",
                }
            ]
        }
    )

    type: str = Field(description="Стабильный URI типа ошибки")
    title: str = Field(description="Краткое название типа ошибки, не зависящее от экземпляра")
    status: int = Field(description="HTTP-код ответа", ge=400, le=599)
    detail: str = Field(description="Описание конкретного случая возникновения ошибки")
    instance: str = Field(description="Путь запроса, при обработке которого возникла ошибка")


class FieldError(BaseModel):
    """Описание одной ошибки валидации поля."""

    field: str = Field(description="Путь к полю запроса", examples=["title"])
    message: str = Field(
        description="Причина отклонения значения",
        examples=["String should have at least 3 characters"],
    )


class ValidationProblemDetails(ProblemDetails):
    """Тело ответа для ошибок валидации запроса (HTTP 422).

    Расширяет базовую структуру членом ``errors`` согласно STD-ERR-05.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "https://docs.local/problems/validation-error",
                    "title": "Request validation failed",
                    "status": 422,
                    "detail": "Request body does not match the expected schema",
                    "instance": "/api/v1/projects",
                    "errors": [
                        {"field": "title", "message": "String should have at least 3 characters"}
                    ],
                }
            ]
        }
    )

    errors: list[FieldError] = Field(
        default_factory=list,
        description="Перечень полей, не прошедших валидацию",
    )
