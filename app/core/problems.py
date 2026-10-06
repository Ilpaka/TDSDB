"""Реестр типов ошибок и их представление по RFC 9457.

Модуль реализует правила STD-ERR-01…STD-ERR-09 стандарта API_STANDARD:
единый реестр типов ошибок, исключение :class:`APIProblem` для сервисного слоя
и централизованные обработчики, формирующие тело ответа.

Роутеры и сервисы не формируют тело ошибки самостоятельно: они возбуждают
:class:`APIProblem` с одной из спецификаций :class:`Problems`.
"""

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.problem import ProblemDetails, ValidationProblemDetails

PROBLEM_BASE_URI = "https://docs.local/problems"
PROBLEM_CONTENT_TYPE = "application/problem+json"


@dataclass(frozen=True)
class ProblemSpec:
    """Спецификация типа ошибки.

    Attributes:
        slug: Идентификатор типа, образующий стабильный URI.
        title: Название типа ошибки, не зависящее от экземпляра.
        status: HTTP-код ответа.
    """

    slug: str
    title: str
    status: int

    @property
    def type_uri(self) -> str:
        """Вернуть стабильный URI типа ошибки."""
        return f"{PROBLEM_BASE_URI}/{self.slug}"


class Problems:
    """Реестр типов ошибок публичного API.

    Соответствует разделу 6.1 стандарта API_STANDARD. Добавление типа
    является совместимым изменением контракта, удаление и переименование —
    несовместимым.
    """

    VALIDATION_ERROR = ProblemSpec(
        "validation-error", "Request validation failed", 422
    )
    AUTHENTICATION_REQUIRED = ProblemSpec(
        "authentication-required", "Authentication required", status.HTTP_401_UNAUTHORIZED
    )
    INVALID_CREDENTIALS = ProblemSpec(
        "invalid-credentials", "Invalid email or password", status.HTTP_401_UNAUTHORIZED
    )
    ACCESS_DENIED = ProblemSpec("access-denied", "Access denied", status.HTTP_403_FORBIDDEN)
    USER_DEACTIVATED = ProblemSpec(
        "user-deactivated", "User account is deactivated", status.HTTP_403_FORBIDDEN
    )
    PROJECT_NOT_FOUND = ProblemSpec(
        "project-not-found", "Project not found", status.HTTP_404_NOT_FOUND
    )
    DOCUMENT_NOT_FOUND = ProblemSpec(
        "document-not-found", "Document not found", status.HTTP_404_NOT_FOUND
    )
    USER_NOT_FOUND = ProblemSpec("user-not-found", "User not found", status.HTTP_404_NOT_FOUND)
    VERSION_NOT_FOUND = ProblemSpec(
        "version-not-found", "Document version not found", status.HTTP_404_NOT_FOUND
    )
    EMAIL_ALREADY_EXISTS = ProblemSpec(
        "email-already-exists", "Email already registered", status.HTTP_409_CONFLICT
    )
    INVALID_STATE_TRANSITION = ProblemSpec(
        "invalid-state-transition", "Invalid document state transition", status.HTTP_409_CONFLICT
    )
    PAYLOAD_TOO_LARGE = ProblemSpec(
        "payload-too-large", "Request body too large", 413
    )
    RATE_LIMIT_EXCEEDED = ProblemSpec(
        "rate-limit-exceeded", "Too many requests", status.HTTP_429_TOO_MANY_REQUESTS
    )
    INTERNAL_ERROR = ProblemSpec(
        "internal-error", "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR
    )


class APIProblem(Exception):
    """Ошибка публичного API, представляемая по RFC 9457.

    Args:
        spec: Спецификация типа ошибки из реестра :class:`Problems`.
        detail: Описание конкретного случая.
        headers: Дополнительные заголовки ответа.
    """

    def __init__(
        self,
        spec: ProblemSpec,
        detail: str,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(detail)
        self.spec = spec
        self.detail = detail
        self.headers = headers


def problem_responses(*specs: ProblemSpec) -> dict[int | str, dict[str, Any]]:
    """Построить секцию ``responses`` операции OpenAPI.

    Args:
        *specs: Типы ошибок, документируемые для операции.

    Returns:
        Отображение HTTP-кода на описание ответа со схемой Problem Details.

    Example:
        >>> responses = problem_responses(
        ...     Problems.AUTHENTICATION_REQUIRED, Problems.PROJECT_NOT_FOUND
        ... )
    """
    responses: dict[int | str, dict[str, Any]] = {}

    for spec in specs:
        model = (
            ValidationProblemDetails
            if spec is Problems.VALIDATION_ERROR
            else ProblemDetails
        )
        responses[spec.status] = {
            "model": model,
            "description": spec.title,
            "content": {PROBLEM_CONTENT_TYPE: {}},
        }

    return responses


def _render(spec: ProblemSpec, detail: str, request: Request, **extra: Any) -> dict[str, Any]:
    """Сформировать тело ответа с ошибкой."""
    body = {
        "type": spec.type_uri,
        "title": spec.title,
        "status": spec.status,
        "detail": detail,
        "instance": request.url.path,
    }
    body.update(extra)
    return body


async def api_problem_handler(request: Request, exc: APIProblem) -> JSONResponse:
    """Представить :class:`APIProblem` в формате Problem Details."""
    return JSONResponse(
        status_code=exc.spec.status,
        content=_render(exc.spec, exc.detail, request),
        media_type=PROBLEM_CONTENT_TYPE,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Привести стандартные исключения HTTP к формату Problem Details.

    Обрабатывает случаи, возбуждаемые самим фреймворком: неизвестный маршрут,
    неподдерживаемый метод, отсутствие заголовка авторизации.
    """
    spec = _SPEC_BY_STATUS.get(exc.status_code) or ProblemSpec(
        slug="http-error",
        title=str(exc.detail),
        status=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_render(spec, str(exc.detail), request),
        media_type=PROBLEM_CONTENT_TYPE,
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Привести ошибки валидации запроса к формату Problem Details."""
    errors = [
        {
            "field": ".".join(str(part) for part in error["loc"][1:]) or str(error["loc"][0]),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    spec = Problems.VALIDATION_ERROR
    return JSONResponse(
        status_code=spec.status,
        content=_render(
            spec,
            "Request does not match the expected schema",
            request,
            errors=errors,
        ),
        media_type=PROBLEM_CONTENT_TYPE,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Скрыть детали необработанного исключения от потребителя API.

    Тело ответа не содержит трассировки стека, текста SQL и внутренних путей
    согласно правилу STD-ERR-06.
    """
    spec = Problems.INTERNAL_ERROR
    return JSONResponse(
        status_code=spec.status,
        content=_render(spec, "Unexpected error while processing the request", request),
        media_type=PROBLEM_CONTENT_TYPE,
    )


_SPEC_BY_STATUS: dict[int, ProblemSpec] = {
    status.HTTP_401_UNAUTHORIZED: Problems.AUTHENTICATION_REQUIRED,
    status.HTTP_403_FORBIDDEN: Problems.ACCESS_DENIED,
    413: Problems.PAYLOAD_TOO_LARGE,
    status.HTTP_429_TOO_MANY_REQUESTS: Problems.RATE_LIMIT_EXCEEDED,
    status.HTTP_500_INTERNAL_SERVER_ERROR: Problems.INTERNAL_ERROR,
}


def register_problem_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики ошибок приложения.

    Args:
        app: Экземпляр приложения FastAPI.
    """
    app.add_exception_handler(APIProblem, api_problem_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
