"""Конфигурация приложения.

Настройки читаются из переменных окружения и файла ``.env``. Модуль
реализует требования безопасности конфигурации: секрет подписи токенов
и список разрешённых origin определяются средой исполнения, а запуск
production с демонстрационными значениями блокируется.
"""

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEMO_JWT_SECRET = "your-super-secret-key-change-in-production"
"""Демонстрационный секрет, допустимый только вне production."""

MIN_PRODUCTION_SECRET_LENGTH = 32
"""Минимальная длина секрета подписи токенов в production."""


class Environment(str, Enum):
    """Среда исполнения приложения."""

    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    """Параметры приложения.

    Attributes:
        ENVIRONMENT: Среда исполнения, определяющая строгость проверок.
        API_V1_PREFIX: Префикс путей публичного контракта версии v1.
        CORS_ORIGINS: Перечень origin, которым разрешены межсайтовые запросы.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Document Center API"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: Environment = Environment.development
    DEBUG: bool = False
    DOCS_ENABLED: bool = Field(
        default=True, description="Публиковать /docs, /redoc и /openapi.json"
    )

    # API contract
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:8000", "http://127.0.0.1:8000"],
        description="Разрешённые origin; символ * в production запрещён",
    )

    # JWT
    JWT_SECRET: str = Field(default=DEMO_JWT_SECRET, repr=False)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=1440)

    # Resource limits
    LOGIN_RATE_LIMIT: int = Field(
        default=10, ge=1, description="Допустимое число попыток входа с одного адреса в окне"
    )
    LOGIN_RATE_WINDOW_SECONDS: int = Field(
        default=60, ge=1, description="Длительность окна ограничения попыток входа, секунд"
    )
    MAX_REQUEST_BODY_BYTES: int = Field(
        default=1_048_576, ge=1024, description="Максимальный размер тела запроса, байт"
    )

    @property
    def is_production(self) -> bool:
        """Признак работы в production."""
        return self.ENVIRONMENT is Environment.production

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Разобрать список origin, заданный строкой через запятую."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _validate_production_safety(self) -> "Settings":
        """Запретить небезопасные значения в production.

        Returns:
            Проверенный набор настроек.

        Raises:
            ValueError: Если конфигурация production содержит демонстрационный
                секрет, слишком короткий секрет, включённый режим отладки
                или безусловный wildcard в списке origin.
        """
        if not self.is_production:
            return self

        if self.JWT_SECRET == DEMO_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET has a demonstration value; set a unique secret for production"
            )

        if len(self.JWT_SECRET) < MIN_PRODUCTION_SECRET_LENGTH:
            raise ValueError(
                "JWT_SECRET must be at least "
                f"{MIN_PRODUCTION_SECRET_LENGTH} characters long in production"
            )

        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS must not contain a wildcard in production")

        if self.DEBUG:
            raise ValueError("DEBUG must be disabled in production")

        return self


@lru_cache
def get_settings() -> Settings:
    """Вернуть параметры приложения.

    Returns:
        Единственный экземпляр настроек, разделяемый приложением.
    """
    return Settings()


settings = get_settings()
