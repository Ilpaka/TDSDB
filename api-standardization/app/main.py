"""Точка входа приложения Document Center API.

Модуль создаёт экземпляр FastAPI, регистрирует обработчики ошибок формата
Problem Details и подключает бизнес-роутеры под префиксом публичного
контракта ``/api/v1`` (правила STD-VER-01 и STD-VER-02 стандарта
API_STANDARD). Служебные операции остаются вне версии.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import register_security_middleware
from app.core.problems import register_problem_handlers
from app.db.session import create_db_and_tables
from app.routers import access, auditlog, auth, documents, projects, users
from app.schemas.service import HealthStatus, ServiceInfo

API_DESCRIPTION = """
Внутренний REST API ИП «Северный Контур» для управления документами по проектам.

**Базовый путь публичного контракта:** `/api/v1`. Версия контракта (`v1`)
не совпадает с версией приложения, указанной в заголовке документации.

### Аутентификация
Получите токен операцией `POST /api/v1/auth/login` и передавайте его в заголовке
`Authorization: Bearer <token>`. В Swagger UI нажмите **Authorize** и вставьте токен.

### Роли
- **admin** — полный доступ ко всем проектам, пользователям и журналу действий;
- **manager** — создаёт проекты и выдаёт доступ участникам своих проектов;
- **worker** — работает с документами в рамках выданного доступа `editor`;
- **viewer** — только чтение в рамках выданного доступа.

### Ошибки
Все ошибки возвращаются в формате RFC 9457 Problem Details
(`application/problem+json`) с полями `type`, `title`, `status`, `detail`,
`instance`; ошибки валидации дополнительно содержат массив `errors`.

### Коллекции
Коллекции поддерживают параметры `offset` (≥ 0) и `limit` (1…100, по умолчанию 20)
и возвращают конверт `items`, `total`, `offset`, `limit`.
"""

OPENAPI_TAGS = [
    {"name": "Authentication", "description": "Вход и получение сведений о текущем пользователе."},
    {"name": "Users", "description": "Учётные записи пользователей. Только для администратора."},
    {"name": "Projects", "description": "Проекты — контейнеры документов и единица разграничения доступа."},
    {"name": "Access", "description": "Доступ участников к проекту: уровни `viewer` и `editor`."},
    {"name": "Documents", "description": "Документы проекта, их жизненный цикл и версии."},
    {"name": "Audit", "description": "Журнал действий пользователей. Только для администратора."},
    {"name": "Health", "description": "Служебные операции вне версии контракта."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подготовить хранилище при запуске приложения."""
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    summary="Документ-центр ИП «Северный Контур»: проекты, документы, версии и аудит",
    description=API_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)


def setup_cors_middleware() -> None:
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


@app.get(
    "/",
    response_model=ServiceInfo,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Получить сведения о сервисе",
    response_description="Название, версии и адреса документации",
    operation_id="get_service_info",
)
def root() -> ServiceInfo:
    """Вернуть метаданные сервиса и адреса документации.

    Операция публичная и не входит в версию контракта.
    """
    return ServiceInfo(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_version="v1",
        base_path=settings.API_V1_PREFIX,
        docs="/docs",
        redoc="/redoc",
        openapi="/openapi.json",
    )


@app.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Проверить работоспособность",
    response_description="Признак работоспособности сервиса",
    operation_id="get_health",
)
def health_check() -> HealthStatus:
    """Вернуть признак работоспособности для систем мониторинга.

    Операция публичная, не обращается к хранилищу и не раскрывает
    сведений о конфигурации.
    """
    return HealthStatus(status="healthy")


def setup_routers() -> None:
    """Подключить бизнес-роутеры под префиксом публичного контракта."""
    prefix = settings.API_V1_PREFIX

    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(projects.router, prefix=prefix)
    app.include_router(access.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(auditlog.router, prefix=prefix)


def main() -> None:
    """Собрать приложение: middleware, обработчики ошибок и маршруты."""
    register_security_middleware(app)
    setup_cors_middleware()
    register_problem_handlers(app)
    setup_routers()


main()
