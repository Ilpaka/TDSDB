"""Общие фикстуры тестов соответствия.

Тесты работают с отдельной временной базой данных SQLite: переменная
окружения ``DATABASE_URL`` задаётся до импорта приложения, поэтому рабочая
база ``app.db`` не затрагивается. Перед каждым тестом схема пересоздаётся,
а состояние ограничителя частоты сбрасывается.
"""

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.mkdtemp(prefix="dc-api-tests-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET"] = "test-secret-key-for-contract-tests-only-0123456789"

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402

from app.core.rate_limit import login_rate_limiter  # noqa: E402
from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

DEFAULT_PASSWORD = "Passw0rd123"


@pytest.fixture(autouse=True)
def clean_state() -> Iterator[None]:
    """Пересоздать схему базы данных и сбросить ограничитель частоты."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    login_rate_limiter.reset()
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    """HTTP-клиент приложения."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_user() -> Callable[..., User]:
    """Фабрика пользователей, создаваемых напрямую в хранилище."""

    def _make_user(role: UserRole, email: str | None = None) -> User:
        with Session(engine) as session:
            user = User(
                email=email or f"{role.value}@example.com",
                password_hash=get_password_hash(DEFAULT_PASSWORD),
                role=role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    return _make_user


def auth_headers(user: User) -> dict[str, str]:
    """Сформировать заголовок авторизации для пользователя."""
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin(make_user) -> User:
    """Администратор."""
    return make_user(UserRole.admin)


@pytest.fixture
def manager(make_user) -> User:
    """Менеджер."""
    return make_user(UserRole.manager)


@pytest.fixture
def worker(make_user) -> User:
    """Сотрудник."""
    return make_user(UserRole.worker)


@pytest.fixture
def viewer(make_user) -> User:
    """Наблюдатель."""
    return make_user(UserRole.viewer)


@pytest.fixture
def project(client, manager) -> dict:
    """Проект, принадлежащий менеджеру."""
    response = client.post(
        "/api/v1/projects",
        json={"title": "Реконструкция котельной", "description": "Тестовый проект"},
        headers=auth_headers(manager),
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def document(client, manager, project) -> dict:
    """Документ в проекте менеджера."""
    response = client.post(
        f"/api/v1/projects/{project['id']}/documents",
        json={"title": "Пояснительная записка", "content": "Раздел 1"},
        headers=auth_headers(manager),
    )
    assert response.status_code == 201
    return response.json()
