"""Схемы служебных операций вне версии контракта."""

from typing import Literal

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Метаданные сервиса и адреса документации."""

    name: str = Field(description="Название сервиса", examples=["Document Center API"])
    version: str = Field(description="Версия приложения (SemVer)", examples=["2.0.0"])
    api_version: str = Field(description="Версия публичного контракта", examples=["v1"])
    base_path: str = Field(description="Базовый путь публичного контракта", examples=["/api/v1"])
    docs: str = Field(description="Адрес Swagger UI", examples=["/docs"])
    redoc: str = Field(description="Адрес ReDoc", examples=["/redoc"])
    openapi: str = Field(description="Адрес OpenAPI-схемы", examples=["/openapi.json"])


class HealthStatus(BaseModel):
    """Признак работоспособности сервиса."""

    status: Literal["healthy"] = Field(description="Состояние сервиса", examples=["healthy"])
