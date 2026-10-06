"""Подключение к базе данных и управление сессиями."""

from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  регистрирует таблицы в метаданных
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)
"""Движок SQLAlchemy, общий для процесса приложения."""


def create_db_and_tables() -> None:
    """Создать отсутствующие таблицы по метаданным моделей."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Выдать сессию базы данных на время обработки запроса.

    Yields:
        Сессия, закрываемая после завершения запроса.
    """
    with Session(engine) as session:
        yield session
