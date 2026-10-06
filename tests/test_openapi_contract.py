"""Проверки OpenAPI-контракта (STD-VER, STD-URI, STD-DOC, STD-SEC-01…02).

Тесты анализируют фактически генерируемую схему ``/openapi.json`` и
экспортированный файл ``docs/openapi/openapi.json``.
"""

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from app.main import app

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
UNVERSIONED_PATHS = {"/", "/health"}
PUBLIC_OPERATIONS = {("post", "/api/v1/auth/login"), ("get", "/"), ("get", "/health")}
ALLOWED_TAGS = {"Authentication", "Users", "Projects", "Access", "Documents", "Audit", "Health"}
EXPORTED_SCHEMA = Path(__file__).resolve().parent.parent / "docs" / "openapi" / "openapi.json"


def _operations(schema: dict) -> list[tuple[str, str, dict]]:
    return [
        (method, path, operation)
        for path, item in schema["paths"].items()
        for method, operation in item.items()
        if method in HTTP_METHODS
    ]


@pytest.fixture(scope="module")
def schema() -> dict:
    """Схема, генерируемая приложением."""
    return app.openapi()


def test_openapi_endpoint_returns_valid_json(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = json.loads(response.text)
    assert body["openapi"].startswith("3.")
    assert body["info"]["title"]
    assert body["info"]["version"]


def test_operation_ids_are_unique(schema):
    ids = [operation.get("operationId") for _, _, operation in _operations(schema)]

    assert all(ids), "every operation must have operationId"
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    assert not duplicates, f"duplicate operationId: {duplicates}"


def test_operation_ids_are_snake_case(schema):
    for method, path, operation in _operations(schema):
        assert re.fullmatch(r"[a-z][a-z0-9_]*", operation["operationId"]), (method, path)


def test_business_paths_start_with_api_v1(schema):
    for path in schema["paths"]:
        if path in UNVERSIONED_PATHS:
            continue
        assert path.startswith("/api/v1/"), f"{path} is outside /api/v1"


def test_no_trailing_slash_and_no_mixed_style(schema):
    paths = set(schema["paths"])

    for path in paths:
        if path == "/":
            continue
        assert not path.endswith("/"), f"{path} has a trailing slash"
        assert path.rstrip("/") + "/" not in paths


def test_paths_are_lowercase_without_verbs(schema):
    verbs = {"grant", "publish", "archive", "restore", "create", "delete", "update", "get"}

    for path in schema["paths"]:
        static_parts = [part for part in path.split("/") if part and not part.startswith("{")]
        for part in static_parts:
            assert part == part.lower(), path
            assert part not in verbs, f"verb '{part}' in {path}"


def test_every_operation_has_tag_summary_and_description(schema):
    for method, path, operation in _operations(schema):
        assert operation.get("tags"), (method, path)
        assert set(operation["tags"]) <= ALLOWED_TAGS, (method, path, operation["tags"])
        assert operation.get("summary"), (method, path)
        assert operation.get("description"), (method, path)


def test_every_operation_documents_success_response(schema):
    for method, path, operation in _operations(schema):
        success = [code for code in operation["responses"] if code.startswith("2")]
        assert success, (method, path)
        for code in success:
            assert operation["responses"][code].get("description"), (method, path, code)


def test_error_responses_use_problem_details(schema):
    for method, path, operation in _operations(schema):
        for code, response in operation["responses"].items():
            if not code.startswith(("4", "5")):
                continue
            content = response.get("content", {})
            assert "application/problem+json" in content or "application/json" in content
            ref = json.dumps(content)
            assert "ProblemDetails" in ref, (method, path, code)


def test_parameters_are_described(schema):
    for method, path, operation in _operations(schema):
        for parameter in operation.get("parameters", []):
            assert parameter.get("description"), (method, path, parameter["name"])


def test_collections_limit_maximum_is_documented(schema):
    for method, path, operation in _operations(schema):
        for parameter in operation.get("parameters", []):
            if parameter["name"] == "limit":
                assert parameter["schema"]["maximum"] == 100, (method, path)
                assert parameter["schema"]["minimum"] == 1, (method, path)


def test_bearer_security_scheme_declared(schema):
    schemes = schema["components"]["securitySchemes"]

    assert any(s.get("type") == "http" and s.get("scheme") == "bearer" for s in schemes.values())


def test_protected_operations_declare_security(schema):
    for method, path, operation in _operations(schema):
        if (method, path) in PUBLIC_OPERATIONS:
            continue
        assert operation.get("security"), f"{method.upper()} {path} has no security requirement"
        assert "401" in operation["responses"], (method, path)


def test_exported_schema_matches_application(schema):
    assert EXPORTED_SCHEMA.exists(), "run scripts/export_openapi.py"
    exported = json.loads(EXPORTED_SCHEMA.read_text(encoding="utf-8"))

    assert exported == json.loads(json.dumps(schema)), (
        "docs/openapi/openapi.json is outdated: run python -m scripts.export_openapi"
    )


def test_schema_properties_have_types(schema):
    typed_keys = {"type", "$ref", "anyOf", "allOf", "oneOf", "enum", "const"}

    for name, component in schema["components"]["schemas"].items():
        for prop, definition in component.get("properties", {}).items():
            assert typed_keys & definition.keys(), f"{name}.{prop} has no type in OpenAPI"


def test_datetime_fields_use_date_time_format(schema):
    project = schema["components"]["schemas"]["ProjectRead"]["properties"]

    assert project["id"]["type"] == "integer"
    assert project["created_at"]["type"] == "string"
    assert project["created_at"]["format"] == "date-time"


def test_descriptions_hide_internal_docstring_sections(schema):
    for method, path, operation in _operations(schema):
        description = operation.get("description", "")
        assert "Args:" not in description, (method, path)
        assert "session" not in description, (method, path)


def test_protected_operations_state_required_access(schema):
    """STD-SEC-04: требуемая роль или уровень доступа указаны в описании."""
    markers = ("администратор", "владельц", "доступ", "admin", "manager", "editor", "viewer")

    for method, path, operation in _operations(schema):
        if (method, path) in PUBLIC_OPERATIONS:
            continue
        description = operation["description"].lower()
        assert any(marker in description for marker in markers), (method, path)
