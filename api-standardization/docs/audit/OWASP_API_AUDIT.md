# OWASP API SECURITY AUDIT — Document Center API

Аудит рисков по перечню **OWASP API Security Top 10 (2023)**.
Перечень используется как база для оценки рисков; сертификатом он не является.

| Параметр | Значение |
|---|---|
| Объект оценки | Document Center API, контракт `/api/v1`, версия приложения `2.0.0` |
| Ветка | `feature/api-v1-standardization` |
| Дата аудита | 2026-09-09 |
| Критерии | OWASP API Security Top 10 2023; `SECURITY_STANDARD.md`; раздел 8 `API_STANDARD.md` |
| Метод | Code review `app/`, инспекция `docs/openapi/openapi.json`, автоматические тесты `tests/test_security_contract.py`, ручные запросы через Swagger UI |

Статусы: **APPLICABLE / NOT APPLICABLE** — применимость категории к объекту;
**PASS / FAIL** — результат проверки после исправлений. В столбце «Baseline»
указан результат для исходного состояния (commit `ccc390a`).

---

## 1. Сводная таблица

| Категория | Применимость | Baseline | Итог | Доказательство | Действие |
|---|---|---|---|---|---|
| API1 Broken Object Level Authorization | APPLICABLE | PASS (частично) | **PASS** | `app/core/permissions.py`; тесты `test_foreign_project_is_hidden`, `test_foreign_document_is_hidden`, `test_viewer_access_allows_read_but_not_write` | Подтверждено тестами; поведение `404` для чужих объектов закреплено в SEC-OBJ-03 |
| API2 Broken Authentication | APPLICABLE | FAIL | **PASS** | `app/core/security.py`, `app/core/config.py:_validate_production_safety`; тесты раздела API2 и `test_production_rejects_unsafe_configuration` | Демонстрационный секрет запрещён в production; `401` + `WWW-Authenticate`; срок токена ограничен |
| API3 Broken Object Property Level Authorization | APPLICABLE | PASS | **PASS** | Схемы `UserRead`, `ProjectCreate`, `DocumentCreate`; тесты `test_user_response_has_no_password_hash`, `test_project_owner_cannot_be_overridden_by_client`, `test_document_author_cannot_be_overridden_by_client` | Закреплено тестами |
| API4 Unrestricted Resource Consumption | APPLICABLE | FAIL | **PASS** | `app/core/rate_limit.py`, `app/core/middleware.py`, `app/schemas/pagination.py`; тесты `test_login_rate_limit_returns_429`, `test_oversized_body_returns_413`, `test_pagination_out_of_range_rejected`, `test_document_content_length_is_limited` | Введены rate limiting входа, лимит тела, единый `limit` ≤ 100, лимит длины содержимого |
| API5 Broken Function Level Authorization | APPLICABLE | **FAIL** | **PASS** | `app/core/deps.py:require_roles`; тесты `test_non_admin_cannot_read_audit_log`, `test_non_admin_cannot_manage_users`, `test_insufficient_role_cannot_create_project` | Исправлен дефект `require_admin`, открывавший журнал аудита всем |
| API6 Unrestricted Access to Sensitive Business Flows | APPLICABLE | PASS (частично) | **PASS** | `access_service.py`, `project_service.py`, `document_service.py`; тест `test_member_cannot_grant_access_or_delete_project`, `test_invalid_state_transition_returns_409` | Выдача доступа, удаление, публикация, архивирование — только владелец/admin или `editor`; все действия в журнале |
| API7 Server Side Request Forgery | **NOT APPLICABLE** | N/A | N/A | `grep` по `app/`: нет `requests`, `httpx`, `urllib`, `aiohttp`, `socket`; ни одна схема не принимает URL | Запрет добавлен как SEC-EXT-01 |
| API8 Security Misconfiguration | APPLICABLE | **FAIL** | **PASS** | `app/main.py:setup_cors_middleware`, `app/core/config.py`, `app/core/middleware.py`, `app/core/problems.py:unhandled_exception_handler`; тесты `test_cors_allows_only_configured_origins`, `test_security_headers_present`, `test_error_body_has_no_internal_details` | CORS по списку, защитные заголовки, проверка production-настроек, ошибки без внутренних деталей |
| API9 Improper Inventory Management | APPLICABLE | FAIL | **PASS** | `docs/audit/ENDPOINT_INVENTORY.md`, `docs/openapi/openapi.json`, `docs/source/versioning.rst`, `CHANGELOG.md`; тесты `test_business_paths_start_with_api_v1`, `test_exported_schema_matches_application` | Версия `/api/v1`, экспорт контракта с контролем актуальности, политика deprecation |
| API10 Unsafe Consumption of APIs | **NOT APPLICABLE** | N/A | N/A | API не обращается к сторонним сервисам (см. API7); входящие данные валидируются Pydantic-схемами | Требования на будущее — SEC-EXT-02 |

**Итог:** 8 применимых категорий — 8 PASS; 2 категории не применимы с обоснованием.

---

## 2. Детализация

### API1 — Broken Object Level Authorization

- **Что проверено:** подмена `project_id` и `document_id` пользователем без доступа
  и пользователем с доступом `viewer`.
- **Реализация:** каждый метод сервиса, принимающий идентификатор проекта или
  документа, вызывает `get_user_project_permission` до чтения данных.
  Пользователь без доступа получает `404` (существование объекта не
  раскрывается); с доступом `viewer` при попытке изменения — `403`.
  Коллекция `GET /api/v1/projects` и значение `total` фильтруются по доступу.
- **Доказательство:**
  - `GET /api/v1/projects/{чужой}` от `worker` → `404 project-not-found`;
  - `GET /api/v1/documents/{чужой}/versions` → `404`;
  - `PATCH`/`DELETE /api/v1/documents/{id}` с доступом `viewer` → `403`.
- **Остаточный риск:** идентификаторы последовательные (целые). Перебор не даёт
  доступа, но позволяет оценить количество объектов; принято как допустимое
  для внутреннего API.

### API2 — Broken Authentication

- **Что проверено:** запросы без токена, с повреждённым и просроченным токеном,
  вход с неверным паролем, деактивированный пользователь, production-настройки.
- **Baseline:** `JWT_SECRET` имел рабочее значение по умолчанию — любой, кто
  видел исходный код, мог выпустить валидный токен администратора.
- **Реализация:** в `production` демонстрационный и короткий секрет блокируют
  запуск; токен с `exp`, по умолчанию 60 минут; пароли — bcrypt; одинаковый
  ответ для неизвестного email и неверного пароля; активность и роль
  пользователя читаются из БД при каждом запросе, поэтому деактивация
  действует немедленно.
- **Доказательство:** `test_protected_endpoint_without_bearer_returns_401`
  (8 операций), `test_invalid_token_returns_401`, `test_expired_token_returns_401`,
  `test_login_with_wrong_password_returns_401`, `test_deactivated_user_is_rejected`,
  `test_production_rejects_unsafe_configuration`.
- **Остаточный риск:** нет механизма отзыва конкретного токена (SEC-AUTH-10,
  РЕКОМЕНДУЕТСЯ); компенсируется коротким сроком жизни и проверкой `is_active`.

### API3 — Broken Object Property Level Authorization

- **Что проверено:** утечка служебных полей в ответах; подмена серверных полей
  в теле запроса (mass assignment).
- **Реализация:** схемы ответа не содержат `password_hash`; схемы запроса
  содержат только изменяемые клиентом поля, поэтому `owner_id`, `created_by`,
  `status` при создании и `granted_by` из тела игнорируются. `UserUpdate`
  (роль и активность) доступна только администратору.
- **Доказательство:** `test_user_response_has_no_password_hash`,
  `test_project_owner_cannot_be_overridden_by_client`,
  `test_document_author_cannot_be_overridden_by_client`.

### API4 — Unrestricted Resource Consumption

- **Baseline:** `limit` до 500 у пользователей; коллекции доступа и версий без
  пагинации; нет ограничений частоты, размера тела, длины содержимого.
- **Реализация:**
  - вход — не более 10 попыток за 60 секунд с адреса, далее `429` + `Retry-After`;
  - тело запроса — не более 1 МиБ, далее `413`;
  - все коллекции — `offset`/`limit`, `limit` ≤ 100, превышение — `422`;
  - содержимое документа ≤ 100 000 символов, названия ≤ 120, описание ≤ 2000.
- **Доказательство:** `test_login_rate_limit_returns_429`,
  `test_rate_limiter_window_expires`, `test_oversized_body_returns_413`,
  `test_pagination_out_of_range_rejected` (9 комбинаций),
  `test_document_content_length_is_limited`.
- **Остаточный риск:** ограничитель хранит состояние в памяти одного процесса;
  общий лимит для аутентифицированных операций не введён (SEC-RL-05 —
  обратный прокси). Зафиксировано в `CERTIFICATION_REPORT.md`.

### API5 — Broken Function Level Authorization

- **Baseline (критический дефект):** `require_admin` возвращал `False`
  вместо отказа, а в `auditlog.py` результат подставлялся в параметр без
  проверки — журнал действий всех пользователей был доступен любому
  аутентифицированному пользователю.
- **Реализация:** единая зависимость `require_roles(*roles)` возбуждает
  `403 access-denied`; применяется через типы `AdminUser` и
  `ProjectManagerUser`. Матрица прав — раздел 2.1 `SECURITY_STANDARD.md`.
- **Доказательство:** `test_non_admin_cannot_read_audit_log` (manager, worker,
  viewer → 403), `test_non_admin_cannot_manage_users`,
  `test_insufficient_role_cannot_create_project`, `test_admin_can_read_audit_log`.

### API6 — Unrestricted Access to Sensitive Business Flows

- **Чувствительные потоки:** выдача и отзыв доступа к проекту, удаление
  проекта, публикация и архивирование документа, изменение роли пользователя.
- **Реализация:** управление доступом и удаление проекта — только владелец
  или `admin`; изменение состояния документа — уровень `editor`; переходы
  состояний ограничены конечным автоматом (`409` для недопустимых);
  каждое действие записывается в журнал аудита (SEC-OBJ-06).
- **Доказательство:** `test_member_cannot_grant_access_or_delete_project`,
  `test_invalid_state_transition_returns_409`, `test_admin_can_read_audit_log`.

### API7 — Server Side Request Forgery — NOT APPLICABLE

API не выполняет исходящих запросов: в `app/` отсутствуют HTTP-клиенты и
сетевые вызовы, ни одно поле схем не принимает URL. Категория не применима.
Появление такой функциональности требует пересмотра (SEC-EXT-01).

### API8 — Security Misconfiguration

- **Baseline:** `allow_origins=["*"]` вместе с `allow_credentials=True`,
  `allow_methods=["*"]`, `allow_headers=["*"]`; демонстрационный секрет по
  умолчанию; нет защитных заголовков.
- **Реализация:** CORS по списку `CORS_ORIGINS`; запрет `*`, `DEBUG=true` и
  слабого секрета в production; `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Cache-Control: no-store`; необработанные исключения →
  `500` без трассировки; `repr` настроек не содержит секрет; `/docs` можно
  отключить через `DOCS_ENABLED`.
- **Доказательство:** `test_cors_allows_only_configured_origins`,
  `test_security_headers_present`, `test_production_rejects_unsafe_configuration`,
  `test_production_accepts_safe_configuration`, `test_error_body_has_no_internal_details`.
- **Остаточный риск:** HSTS и TLS настраиваются на обратном прокси и в
  приложении не проверяются.

### API9 — Improper Inventory Management

- **Baseline:** версия контракта отсутствовала, схема не экспортировалась,
  политики устаревания не было, часть кода (`delete_project`) не была выведена
  в контракт.
- **Реализация:** все бизнес-операции под `/api/v1`; полная инвентаризация в
  `ENDPOINT_INVENTORY.md`; контракт экспортируется в `docs/openapi/openapi.json`,
  тест сверяет его с приложением; процедура deprecation — `versioning.rst`;
  несовместимые изменения — раздел `Breaking` в `CHANGELOG.md`.
- **Доказательство:** `test_business_paths_start_with_api_v1`,
  `test_no_trailing_slash_and_no_mixed_style`, `test_exported_schema_matches_application`.

### API10 — Unsafe Consumption of APIs — NOT APPLICABLE

API не потребляет сторонние API (см. API7). Все входящие данные клиента
валидируются Pydantic-схемами с ограничениями. Требования на случай появления
интеграций — SEC-EXT-02 (тайм-ауты, валидация ответа, TLS).
