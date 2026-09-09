"""Аутентификация и авторизация запросов.

Модуль реализует выпуск и проверку токенов Bearer/JWT и определяет
зависимость получения текущего пользователя. Отсутствующий или
недействительный токен приводит к ответу 401 с заголовком
``WWW-Authenticate``, недостаточность прав — к ответу 403
(правила STD-SEC-05 и STD-SEC-08 стандарта API_STANDARD).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Session

from app.core.config import settings
from app.core.problems import APIProblem, Problems
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)
"""Схема Bearer без автоматической ошибки: код 401 формируется явно."""

_UNAUTHENTICATED_HEADERS = {"WWW-Authenticate": "Bearer"}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить соответствие пароля сохранённому хэшу.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Ранее сохранённый хэш.

    Returns:
        Признак совпадения пароля.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Вычислить хэш пароля.

    Args:
        password: Пароль в открытом виде.

    Returns:
        Хэш пароля, пригодный для хранения.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Выпустить токен доступа.

    Args:
        data: Полезная нагрузка токена.
        expires_delta: Срок действия; при отсутствии применяется значение
            параметра ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        Подписанный JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta 
    
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Разобрать и проверить токен доступа.

    Args:
        token: Значение токена без префикса схемы.

    Returns:
        Полезная нагрузка токена либо ``None``, если токен недействителен
        или истёк.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: Session = Depends(get_session),
):
    """Вернуть пользователя, которому принадлежит токен запроса.

    Args:
        credentials: Учётные данные схемы Bearer.
        session: Сессия базы данных.

    Returns:
        Аутентифицированный пользователь.

    Raises:
        APIProblem: Если токен отсутствует, недействителен либо учётная
            запись деактивирована.
    """
    from app.models.user import User

    unauthenticated = APIProblem(
        Problems.AUTHENTICATION_REQUIRED,
        "Valid Bearer token is required to access this operation",
        headers=_UNAUTHENTICATED_HEADERS,
    )

    if credentials is None:
        raise unauthenticated

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise unauthenticated

    user_id = payload.get("user_id")

    if user_id is None:
        raise unauthenticated

    user = session.get(User, user_id)

    if user is None:
        raise unauthenticated

    if not user.is_active:
        raise APIProblem(
            Problems.USER_DEACTIVATED,
            "User account is deactivated",
        )

    return user


def require_roles(*allowed_roles: str):
    """Создать зависимость, допускающую только перечисленные роли.

    Args:
        *allowed_roles: Роли, которым разрешена операция.

    Returns:
        Зависимость FastAPI, возвращающая текущего пользователя.
    """

    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Operation requires one of the following roles: "
                + ", ".join(allowed_roles),
            )
        return current_user

    return role_checker


def require_admin(current_user=Depends(get_current_user)):
    """Допустить к операции только администратора.

    Args:
        current_user: Аутентифицированный пользователь.

    Returns:
        Пользователь с ролью администратора.

    Raises:
        APIProblem: Если роль пользователя отличается от ``admin``.
    """
    if current_user.role != "admin":
        raise APIProblem(
            Problems.ACCESS_DENIED,
            "Operation requires the admin role",
        )
    return current_user
