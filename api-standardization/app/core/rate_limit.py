"""Ограничение частоты запросов.

Модуль реализует правило STD-SEC-09 стандарта API_STANDARD и требование
SEC-RL-01 стандарта SECURITY_STANDARD: число попыток входа с одного
адреса ограничено скользящим окном. При превышении лимита возвращается
ответ 429 в формате Problem Details с заголовком ``Retry-After``.

Ограничитель хранит состояние в памяти процесса и рассчитан на запуск
приложения в одном процессе. Для горизонтального масштабирования
хранилище окон выносится во внешний сервис (например, Redis); это
решение зафиксировано в ``SECURITY_STANDARD.md``.
"""

import math
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable

from fastapi import Request

from app.core.config import settings
from app.core.problems import APIProblem, Problems


class SlidingWindowRateLimiter:
    """Ограничитель частоты событий по ключу на основе скользящего окна.

    Args:
        max_requests: Допустимое число событий в окне.
        window_seconds: Длительность окна в секундах.
        clock: Источник монотонного времени; подменяется в тестах.
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str) -> int:
        """Зарегистрировать событие и проверить лимит.

        Args:
            key: Ключ, по которому ведётся учёт (например, адрес клиента).

        Returns:
            ``0``, если событие допустимо; иначе число секунд до момента,
            когда событие станет допустимым.
        """
        now = self._clock()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()

            if len(events) >= self.max_requests:
                return max(1, math.ceil(self.window_seconds - (now - events[0])))

            events.append(now)
            return 0

    def reset(self) -> None:
        """Очистить накопленные события всех ключей."""
        with self._lock:
            self._events.clear()


login_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.LOGIN_RATE_LIMIT,
    window_seconds=settings.LOGIN_RATE_WINDOW_SECONDS,
)
"""Ограничитель попыток входа, общий для процесса приложения."""


def limit_login_attempts(request: Request) -> None:
    """Зависимость FastAPI, ограничивающая частоту попыток входа.

    Args:
        request: Текущий HTTP-запрос.

    Raises:
        APIProblem: Если лимит попыток для адреса клиента исчерпан.
    """
    client = request.client.host if request.client else "unknown"
    retry_after = login_rate_limiter.hit(client)

    if retry_after:
        raise APIProblem(
            Problems.RATE_LIMIT_EXCEEDED,
            f"Too many login attempts; retry in {retry_after} seconds",
            headers={"Retry-After": str(retry_after)},
        )
