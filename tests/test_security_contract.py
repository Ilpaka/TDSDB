"""Проверки безопасности (STD-SEC, SECURITY_STANDARD, OWASP API Top 10).

Тесты подтверждают аутентификацию, разграничение по ролям,
object-level authorization, ограничения ресурсов и безопасную
конфигурацию production.
"""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.config import DEMO_JWT_SECRET, Settings
from app.core.middleware import SECURITY_HEADERS
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.security import create_access_token
from tests.conftest import DEFAULT_PASSWORD, auth_headers
from tests.test_http_contract import assert_problem

PROTECTED_ENDPOINTS = [
    ("get", "/api/v1/auth/me"),
    ("get", "/api/v1/users"),
    ("get", "/api/v1/projects"),
    ("post", "/api/v1/projects"),
    ("get", "/api/v1/projects/1"),
    ("get", "/api/v1/projects/1/documents"),
    ("get", "/api/v1/documents/1"),
    ("get", "/api/v1/audit"),
]

STRONG_SECRET = "s" * 48


# --- API2: Broken Authentication -------------------------------------------


@pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
def test_protected_endpoint_without_bearer_returns_401(client, method, url):
    response = client.request(method, url)

    assert_problem(response, 401, "authentication-required")
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_token_returns_401(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert_problem(response, 401, "authentication-required")


def test_expired_token_returns_401(client, admin):
    token = create_access_token(
        {"user_id": admin.id, "role": "admin"}, expires_delta=timedelta(seconds=-1)
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert_problem(response, 401)


def test_login_returns_bearer_token(client, admin):
    response = client.post(
        "/api/v1/auth/login", json={"email": admin.email, "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.json()["email"] == admin.email


def test_login_with_wrong_password_returns_401(client, admin):
    response = client.post(
        "/api/v1/auth/login", json={"email": admin.email, "password": "Wrong1234"}
    )

    assert_problem(response, 401, "invalid-credentials")


def test_deactivated_user_is_rejected(client, admin, viewer):
    client.patch(
        f"/api/v1/users/{viewer.id}", json={"is_active": False}, headers=auth_headers(admin)
    )

    assert_problem(
        client.get("/api/v1/auth/me", headers=auth_headers(viewer)), 403, "user-deactivated"
    )


# --- API5: Broken Function Level Authorization -----------------------------


@pytest.mark.parametrize("role", ["manager", "worker", "viewer"])
def test_non_admin_cannot_read_audit_log(client, request, role):
    user = request.getfixturevalue(role)

    assert_problem(client.get("/api/v1/audit", headers=auth_headers(user)), 403, "access-denied")


@pytest.mark.parametrize("role", ["manager", "worker", "viewer"])
def test_non_admin_cannot_manage_users(client, request, role):
    user = request.getfixturevalue(role)
    headers = auth_headers(user)

    assert_problem(client.get("/api/v1/users", headers=headers), 403)
    assert_problem(
        client.post(
            "/api/v1/users",
            json={"email": "new@example.com", "password": "Passw0rd123"},
            headers=headers,
        ),
        403,
    )


@pytest.mark.parametrize("role", ["worker", "viewer"])
def test_insufficient_role_cannot_create_project(client, request, role):
    user = request.getfixturevalue(role)

    response = client.post(
        "/api/v1/projects", json={"title": "Чужой проект"}, headers=auth_headers(user)
    )

    assert_problem(response, 403, "access-denied")


def test_admin_can_read_audit_log(client, admin, project):
    response = client.get("/api/v1/audit", headers=auth_headers(admin))

    assert response.status_code == 200
    assert any(item["action"] == "create_project" for item in response.json()["items"])


# --- API1: Broken Object Level Authorization -------------------------------


def test_foreign_project_is_hidden(client, worker, project):
    headers = auth_headers(worker)

    assert_problem(client.get(f"/api/v1/projects/{project['id']}", headers=headers), 404)
    assert_problem(client.get(f"/api/v1/projects/{project['id']}/documents", headers=headers), 404)
    assert client.get("/api/v1/projects", headers=headers).json()["total"] == 0


def test_foreign_document_is_hidden(client, worker, document):
    headers = auth_headers(worker)

    assert_problem(client.get(f"/api/v1/documents/{document['id']}", headers=headers), 404)
    assert_problem(
        client.get(f"/api/v1/documents/{document['id']}/versions", headers=headers), 404
    )


def test_viewer_access_allows_read_but_not_write(client, manager, worker, project, document):
    client.put(
        f"/api/v1/projects/{project['id']}/access/{worker.id}",
        json={"permission": "viewer"},
        headers=auth_headers(manager),
    )
    headers = auth_headers(worker)

    assert client.get(f"/api/v1/documents/{document['id']}", headers=headers).status_code == 200
    assert_problem(
        client.patch(
            f"/api/v1/documents/{document['id']}", json={"title": "Изменено"}, headers=headers
        ),
        403,
    )
    assert_problem(
        client.delete(f"/api/v1/documents/{document['id']}", headers=headers), 403
    )


def test_editor_access_allows_document_changes(client, manager, worker, project, document):
    client.put(
        f"/api/v1/projects/{project['id']}/access/{worker.id}",
        json={"permission": "editor"},
        headers=auth_headers(manager),
    )

    response = client.patch(
        f"/api/v1/documents/{document['id']}",
        json={"title": "Изменено сотрудником"},
        headers=auth_headers(worker),
    )

    assert response.status_code == 200


# --- API6: Sensitive Business Flows ----------------------------------------


def test_member_cannot_grant_access_or_delete_project(client, manager, worker, viewer, project):
    client.put(
        f"/api/v1/projects/{project['id']}/access/{worker.id}",
        json={"permission": "editor"},
        headers=auth_headers(manager),
    )
    headers = auth_headers(worker)

    assert_problem(
        client.put(
            f"/api/v1/projects/{project['id']}/access/{viewer.id}",
            json={"permission": "editor"},
            headers=headers,
        ),
        403,
    )
    assert_problem(client.delete(f"/api/v1/projects/{project['id']}", headers=headers), 403)


# --- API3: Broken Object Property Level Authorization ----------------------


def test_project_owner_cannot_be_overridden_by_client(client, manager, worker):
    response = client.post(
        "/api/v1/projects",
        json={"title": "Проект", "owner_id": worker.id},
        headers=auth_headers(manager),
    )

    assert response.status_code == 201
    assert response.json()["owner_id"] == manager.id


def test_document_author_cannot_be_overridden_by_client(client, manager, worker, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/documents",
        json={"title": "Документ", "created_by": worker.id, "status": "published"},
        headers=auth_headers(manager),
    )

    assert response.status_code == 201
    assert response.json()["created_by"] == manager.id
    assert response.json()["status"] == "draft"


# --- API4: Unrestricted Resource Consumption -------------------------------


def test_login_rate_limit_returns_429(client, admin):
    payload = {"email": admin.email, "password": "Wrong1234"}
    responses = [client.post("/api/v1/auth/login", json=payload) for _ in range(11)]

    assert all(r.status_code == 401 for r in responses[:10])
    assert_problem(responses[10], 429, "rate-limit-exceeded")
    assert int(responses[10].headers["retry-after"]) >= 1


def test_rate_limiter_window_expires():
    now = [0.0]
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60, clock=lambda: now[0])

    assert limiter.hit("client") == 0
    assert limiter.hit("client") == 0
    assert limiter.hit("client") == 60
    now[0] = 60.0
    assert limiter.hit("client") == 0


def test_oversized_body_returns_413(client, manager):
    response = client.post(
        "/api/v1/projects",
        content=b"{" + b" " * 2_000_000 + b"}",
        headers={**auth_headers(manager), "Content-Type": "application/json"},
    )

    assert_problem(response, 413, "payload-too-large")


def test_document_content_length_is_limited(client, manager, project):
    response = client.post(
        f"/api/v1/projects/{project['id']}/documents",
        json={"title": "Большой документ", "content": "x" * 100_001},
        headers=auth_headers(manager),
    )

    assert_problem(response, 422, "validation-error")


# --- API8: Security Misconfiguration ---------------------------------------


def test_security_headers_present(client):
    response = client.get("/health")

    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value


def test_cors_allows_only_configured_origins(client):
    allowed = client.options(
        "/api/v1/projects",
        headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "GET"},
    )
    denied = client.options(
        "/api/v1/projects",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:8000"
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"JWT_SECRET": DEMO_JWT_SECRET}, "demonstration"),
        ({"JWT_SECRET": "short"}, "at least"),
        ({"JWT_SECRET": STRONG_SECRET, "CORS_ORIGINS": "*"}, "wildcard"),
        ({"JWT_SECRET": STRONG_SECRET, "DEBUG": True}, "DEBUG"),
    ],
)
def test_production_rejects_unsafe_configuration(overrides, message):
    with pytest.raises(ValidationError, match=message):
        Settings(_env_file=None, ENVIRONMENT="production", **overrides)


def test_production_accepts_safe_configuration():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET=STRONG_SECRET,
        CORS_ORIGINS="https://docs.severny-kontur.example",
    )

    assert settings.is_production
    assert STRONG_SECRET not in repr(settings)
