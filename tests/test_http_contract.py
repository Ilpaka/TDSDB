"""Проверки HTTP-контракта (STD-HTTP, STD-COL, STD-ERR, STD-DATA).

Тесты выполняют реальные запросы через ``TestClient`` и проверяют коды
ответов, структуру тел, пагинацию и формат ошибок.
"""

import re

import pytest

from tests.conftest import auth_headers

PROBLEM_FIELDS = {"type", "title", "status", "detail", "instance"}
RFC3339_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def assert_problem(response, status: int, slug: str | None = None) -> dict:
    """Проверить, что ответ — Problem Details с указанным кодом."""
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert PROBLEM_FIELDS <= body.keys()
    assert body["status"] == status
    assert body["type"].startswith("https://docs.local/problems/")
    assert body["instance"] == response.request.url.path
    if slug:
        assert body["type"].endswith(f"/{slug}")
    return body


def test_health_and_service_info(client):
    assert client.get("/health").json() == {"status": "healthy"}

    info = client.get("/").json()
    assert info["api_version"] == "v1"
    assert info["base_path"] == "/api/v1"


def test_create_returns_201_with_resource(client, project):
    assert project["id"] >= 1
    assert project["title"] == "Реконструкция котельной"


def test_get_returns_200(client, manager, project):
    response = client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers(manager))

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


def test_patch_returns_200_and_keeps_unspecified_fields(client, manager, project):
    response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"title": "Новое название"},
        headers=auth_headers(manager),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Новое название"
    assert response.json()["description"] == project["description"]


@pytest.mark.parametrize("resource", ["project", "document"])
def test_delete_returns_204_without_body(client, manager, project, document, resource):
    url = (
        f"/api/v1/projects/{project['id']}"
        if resource == "project"
        else f"/api/v1/documents/{document['id']}"
    )

    response = client.delete(url, headers=auth_headers(manager))

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url, headers=auth_headers(manager)).status_code == 404


def test_unknown_resource_returns_404_problem(client, admin):
    body = assert_problem(
        client.get("/api/v1/projects/999999", headers=auth_headers(admin)),
        404,
        "project-not-found",
    )
    assert body["title"] == "Project not found"

    assert_problem(
        client.get("/api/v1/documents/999999", headers=auth_headers(admin)),
        404,
        "document-not-found",
    )


def test_unknown_route_returns_404_problem(client):
    assert_problem(client.get("/api/v1/no-such-resource"), 404)


def test_trailing_slash_is_not_an_alias(client, admin):
    response = client.get(
        "/api/v1/projects/", headers=auth_headers(admin), follow_redirects=False
    )

    assert response.status_code != 200


def test_collection_envelope(client, manager, project):
    response = client.get("/api/v1/projects", headers=auth_headers(manager))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "offset", "limit"}
    assert body["total"] == 1
    assert body["offset"] == 0
    assert body["limit"] == 20


def test_pagination_offset_and_limit(client, manager):
    headers = auth_headers(manager)
    for number in range(5):
        client.post("/api/v1/projects", json={"title": f"Проект {number}"}, headers=headers)

    body = client.get("/api/v1/projects?offset=2&limit=2", headers=headers).json()

    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["offset"] == 2
    assert body["limit"] == 2


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/projects",
        "/api/v1/users",
        "/api/v1/audit",
    ],
)
@pytest.mark.parametrize("query", ["limit=101", "limit=0", "offset=-1"])
def test_pagination_out_of_range_rejected(client, admin, url, query):
    body = assert_problem(
        client.get(f"{url}?{query}", headers=auth_headers(admin)),
        422,
        "validation-error",
    )
    assert body["errors"], "validation problem must list errors"
    assert {"field", "message"} <= body["errors"][0].keys()


def test_validation_error_lists_fields(client, manager):
    body = assert_problem(
        client.post("/api/v1/projects", json={"title": "ab"}, headers=auth_headers(manager)),
        422,
        "validation-error",
    )

    assert any(error["field"] == "title" for error in body["errors"])


def test_conflict_on_duplicate_email(client, admin, viewer):
    response = client.post(
        "/api/v1/users",
        json={"email": viewer.email, "password": "Another123", "role": "viewer"},
        headers=auth_headers(admin),
    )

    assert_problem(response, 409, "email-already-exists")


def test_invalid_state_transition_returns_409(client, manager, document):
    url = f"/api/v1/documents/{document['id']}"
    headers = auth_headers(manager)

    assert client.patch(url, json={"status": "archived"}, headers=headers).status_code == 200
    assert_problem(
        client.patch(url, json={"status": "published"}, headers=headers),
        409,
        "invalid-state-transition",
    )


def test_put_access_returns_201_then_200(client, manager, worker, project):
    url = f"/api/v1/projects/{project['id']}/access/{worker.id}"
    headers = auth_headers(manager)

    created = client.put(url, json={"permission": "viewer"}, headers=headers)
    updated = client.put(url, json={"permission": "editor"}, headers=headers)

    assert created.status_code == 201
    assert updated.status_code == 200
    assert updated.json()["permission"] == "editor"


def test_datetimes_are_rfc3339_utc(client, manager, project, document):
    assert RFC3339_UTC.match(project["created_at"]), project["created_at"]
    assert RFC3339_UTC.match(document["created_at"]), document["created_at"]
    assert RFC3339_UTC.match(document["updated_at"]), document["updated_at"]

    me = client.get("/api/v1/auth/me", headers=auth_headers(manager)).json()
    assert RFC3339_UTC.match(me["created_at"])


def test_json_fields_are_snake_case(client, manager, document):
    for key in document:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", key), key


def test_user_response_has_no_password_hash(client, admin, viewer):
    body = client.get("/api/v1/users", headers=auth_headers(admin)).json()

    for user in body["items"]:
        assert "password" not in user
        assert "password_hash" not in user


def test_document_versions_are_created_and_restored(client, manager, document):
    url = f"/api/v1/documents/{document['id']}"
    headers = auth_headers(manager)
    client.patch(url, json={"content": "Раздел 2"}, headers=headers)

    versions = client.get(f"{url}/versions", headers=headers).json()
    assert versions["total"] == 2

    restored = client.post(f"{url}/versions", json={"restore_from": 1}, headers=headers)
    assert restored.status_code == 201
    assert client.get(url, headers=headers).json()["content"] == "Раздел 1"

    assert_problem(
        client.get(f"{url}/versions/99", headers=headers), 404, "version-not-found"
    )


def test_error_body_has_no_internal_details(client, admin):
    response = client.get("/api/v1/projects/999999", headers=auth_headers(admin))
    text = response.text.lower()

    for marker in ("traceback", "select ", "sqlite", "app/", ".py", "jwt_secret"):
        assert marker not in text
