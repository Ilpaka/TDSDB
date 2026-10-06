"""Middleware защиты HTTP-уровня.

Модуль реализует требования SEC-RL-02 и SEC-CFG-05 стандарта
SECURITY_STANDARD: ограничение размера тела запроса и защитные заголовки
ответа. Ограничения применяются ко всем операциям до входа в роутеры.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.problems import PROBLEM_CONTENT_TYPE, Problems

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}
"""Заголовки, добавляемые к каждому ответу API."""

_DOCS_PATHS = frozenset({"/docs", "/redoc", "/docs/oauth2-redirect"})


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Отклонить запрос, объявленный размер тела которого превышает лимит.

    Args:
        app: Оборачиваемое ASGI-приложение.
        max_body_bytes: Максимально допустимый размер тела, байт.
    """

    def __init__(self, app, max_body_bytes: int) -> None:
        super().__init__(app)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Проверить заголовок ``Content-Length`` до чтения тела."""
        content_length = request.headers.get("content-length")

        if content_length and content_length.isdigit() and int(content_length) > self.max_body_bytes:
            spec = Problems.PAYLOAD_TOO_LARGE
            return JSONResponse(
                status_code=spec.status,
                media_type=PROBLEM_CONTENT_TYPE,
                content={
                    "type": spec.type_uri,
                    "title": spec.title,
                    "status": spec.status,
                    "detail": f"Request body must not exceed {self.max_body_bytes} bytes",
                    "instance": request.url.path,
                },
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Добавить защитные заголовки к ответам API.

    Страницы Swagger UI и ReDoc загружают ресурсы с CDN и встраиваются
    в браузер, поэтому для них заголовки кэширования не применяются.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Выполнить запрос и дополнить заголовки ответа."""
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            if name == "Cache-Control" and request.url.path in _DOCS_PATHS:
                continue
            response.headers.setdefault(name, value)
        return response


def register_security_middleware(app: FastAPI) -> None:
    """Подключить middleware защиты HTTP-уровня.

    Args:
        app: Экземпляр приложения FastAPI.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=settings.MAX_REQUEST_BODY_BYTES)
