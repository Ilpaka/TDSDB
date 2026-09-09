"""Точка входа приложения Document Center API.

Модуль создаёт экземпляр FastAPI, регистрирует обработчики ошибок формата
Problem Details и подключает бизнес-роутеры под префиксом публичного
контракта ``/api/v1`` (правила STD-VER-01 и STD-VER-02 стандарта
API_STANDARD). Служебные операции остаются вне версии.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.problems import register_problem_handlers
from app.db.session import create_db_and_tables
from app.routers import access, auditlog, auth, documents, projects, users



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подготовить хранилище при запуске приложения."""
    create_db_and_tables()
    yield

app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
            ## Документ-центр API для ИП «Северный Контур»

            Внутренний веб-API сервис для управления документами по проектам.

            ### Возможности:
            - **Аутентификация** - JWT токены, bcrypt хеширование паролей
            - **Роли** - admin, manager, worker, viewer
            - **Проекты** - создание, редактирование, управление доступом
            - **Документы** - создание, редактирование, публикация, архивирование
            - **Версионирование** - автоматическое сохранение версий документов
            - **Аудит** - журнал всех действий пользователей

            ### Роли:
            - **admin** - полный доступ ко всем проектам и пользователям
            - **manager** - ведёт проекты, выдаёт доступ участникам своих проектов  
            - **worker** - читает и редактирует документы в рамках доступа "editor"
            - **viewer** - только чтение в рамках выданного доступа
    """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

def setup_cors_middleware():
    """Настроить CORS по списку origin, заданному средой исполнения.

    Безусловный wildcard не применяется: перечень разрешённых origin
    определяется параметром ``CORS_ORIGINS`` и проверяется при старте.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

@app.get("/", tags=["Root"], operation_id="get_service_info")
def root():
    """Вернуть метаданные сервиса и адреса документации."""
    return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "api_version": "v1",
            "base_path": settings.API_V1_PREFIX,
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        }

@app.get("/health", tags=["Health"], operation_id="get_health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def setup_routers() -> None:
    """Подключить бизнес-роутеры под префиксом публичного контракта."""
    prefix = settings.API_V1_PREFIX

    app.include_router(users.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(projects.router, prefix=prefix)
    app.include_router(access.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(auditlog.router, prefix=prefix)


def main() -> None:
    """Собрать приложение: middleware, обработчики ошибок и маршруты."""
    setup_cors_middleware()
    register_problem_handlers(app)
    setup_routers()


main()


