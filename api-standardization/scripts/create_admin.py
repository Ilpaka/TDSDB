"""Создать первую учётную запись администратора.

Публичная регистрация в API v1 отсутствует: пользователей создаёт
администратор операцией ``POST /api/v1/users``. Скрипт решает задачу
начальной инициализации пустой базы данных и запускается оператором
на сервере, а не через HTTP.

Пароль не передаётся аргументом командной строки, чтобы он не попал
в историю оболочки: он читается из переменной окружения
``ADMIN_PASSWORD`` либо запрашивается интерактивно.

Пример::

    python -m scripts.create_admin --email admin@example.com
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import create_db_and_tables, engine  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402


def create_admin(email: str, password: str) -> User:
    """Создать администратора с указанными учётными данными.

    Args:
        email: Адрес электронной почты администратора.
        password: Пароль, удовлетворяющий политике сложности.

    Returns:
        Созданная учётная запись.

    Raises:
        ValueError: Если адрес уже зарегистрирован или данные не прошли
            валидацию схемы ``UserCreate``.
    """
    try:
        data = UserCreate(email=email, password=password, role=UserRole.admin)
    except ValidationError as exc:
        raise ValueError(exc.errors()[0]["msg"]) from exc

    create_db_and_tables()
    with Session(engine) as session:
        if session.exec(select(User).where(User.email == data.email)).first():
            raise ValueError(f"User {data.email} already exists")

        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            role=UserRole.admin,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def main() -> int:
    """Разобрать аргументы и создать администратора.

    Returns:
        Код завершения процесса.
    """
    parser = argparse.ArgumentParser(description="Create the first administrator account")
    parser.add_argument("--email", required=True, help="Administrator email")
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password: ")

    try:
        user = create_admin(args.email, password)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Administrator {user.email} created with id={user.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
