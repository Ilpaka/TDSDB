# Changelog

Формат — [Keep a Changelog 1.1.0](https://keepachangelog.com/ru/1.1.0/),
версии приложения — [SemVer 2.0.0](https://semver.org/lang/ru/).
Версия приложения и версия контракта (`/api/v1`) независимы.

## [2.0.0] — 2026-09-09

Первый выпуск стандартизированного контракта `/api/v1`.

### Breaking

Все изменения ниже несовместимы с клиентами версии 1.0.0.

| Было (1.0.0) | Стало (2.0.0) |
|---|---|
| Операции без префикса: `/projects`, `/auth/login`, … | Все бизнес-операции под `/api/v1`: `/api/v1/projects`, `/api/v1/auth/login`, … |
| `GET /projects/`, `GET /users/` (со слэшем) | `GET /api/v1/projects`, `GET /api/v1/users` — без завершающего слэша; путь со слэшем не является псевдонимом |
| `POST /auth/register` | `POST /api/v1/users` (только `admin`); публичной регистрации нет |
| `POST /projects/{id}/access/grant` | `PUT /api/v1/projects/{id}/access/{user_id}` с телом `{"permission": "..."}`; `201` при создании, `200` при изменении |
| `POST /documents/{id}/publish` | `PATCH /api/v1/documents/{id}` с телом `{"status": "published"}` |
| `POST /documents/{id}/archive` | `PATCH /api/v1/documents/{id}` с телом `{"status": "archived"}` |
| `POST /documents/{id}/versions/{v}/restore` | `POST /api/v1/documents/{id}/versions` с телом `{"restore_from": v}`, код `201` |
| Путь-параметр `{doc_id}` | `{document_id}` |
| Параметр пагинации `skip` | `offset` |
| Коллекции возвращают массив `[...]` | Конверт `{"items": [...], "total": N, "offset": O, "limit": L}` |
| `limit` до 500 у `/users`; превышение молча усекалось | `limit` 1…100 у всех коллекций; выход за диапазон — `422` |
| Ошибки `{"detail": "..."}` / `{"detail": [...]}` | RFC 9457 Problem Details, `Content-Type: application/problem+json` |
| Занятый email — `400` | `409 email-already-exists` |
| Дата и время без часового пояса | RFC 3339 UTC с суффиксом `Z` |
| Запуск с демонстрационным `JWT_SECRET` в любой среде | В `production` запуск блокируется (см. Security) |

**Миграция клиента:** добавить префикс `/api/v1` к базовому URL; заменить
перечисленные операции; читать коллекции из поля `items`; переименовать `skip`
в `offset`; разбирать ошибки по полям `status`, `type`, `detail`, а для `422` —
по массиву `errors`.

### Added

- Операции `DELETE /api/v1/projects/{project_id}` и `DELETE /api/v1/documents/{document_id}` (`204`).
- `PATCH /api/v1/users/{user_id}`: изменение роли и деактивация пользователя.
- `GET /api/v1/users`: отбор по роли; `GET /api/v1/projects/{id}/documents`: отбор по `status`.
- Пагинация коллекций доступа к проекту и версий документа.
- Возврат документа из `archived` в `draft`.
- Реестр типов ошибок `app/core/problems.py` и централизованные обработчики.
- Стабильные `operationId`, `summary`, описания, `responses` и примеры для всех операций; описания тегов.
- Схемы ответов `ServiceInfo` и `HealthStatus` для `/` и `/health`.
- Скрипт `scripts/create_admin.py` для создания первого администратора.
- Скрипт `scripts/export_openapi.py` и контракт `docs/openapi/openapi.json`.
- Контрактные тесты и тесты безопасности (`tests/`, 83 проверки).
- Документация Sphinx (`docs/source/`), стандарты (`docs/standards/`), аудит (`docs/audit/`).
- `README.md`, `SECURITY.md`, `CHANGELOG.md`, шаблон Pull Request.

### Changed

- Проверка роли выполняется зависимостью `require_roles`, возбуждающей `403`.
- Сессия БД в `get_current_user` получается через систему зависимостей FastAPI.
- Все ORM-модели регистрируются при импорте пакета `app.models`.
- Frontend переведён на базовый URL `/api/v1`.
- Версия приложения: `1.0.0` → `2.0.0`.

### Deprecated

- Нет. Устаревших операций в контракте `v1` нет; процедура deprecation описана
  в `docs/source/versioning.rst`.

### Removed

- `POST /auth/register`, `POST /projects/{id}/access/grant`,
  `POST /documents/{id}/publish`, `POST /documents/{id}/archive`,
  `POST /documents/{id}/versions/{v}/restore` — заменены (см. Breaking).

### Fixed

- `GET /audit` был неработоспособен: в запрос передавалась Pydantic-схема вместо модели.
- Регулярное выражение проверки пароля не компилировалось.
- Хэш пароля возвращался как `bytes` при аннотации `str`.
- Файл `app/schemas/__initi__.py` переименован в `__init__.py`.
- Повторная выдача доступа возвращала `201` вместо `200`.

### Security

- **Журнал действий был доступен любому пользователю**: `require_admin`
  возвращал `False` вместо отказа. Теперь `GET /api/v1/audit` — только `admin` (OWASP API5).
- `JWT_SECRET` берётся из окружения; в production запрещены демонстрационный
  и короткий (< 32 символов) секрет, `DEBUG=true`, `CORS_ORIGINS=*`.
- CORS: вместо `*` с `allow_credentials=True` — список origin из настроек,
  ограниченный набор методов и заголовков.
- Ограничение попыток входа: 10 за 60 секунд с адреса, далее `429` с `Retry-After`.
- Ограничение размера тела запроса (1 МиБ, `413`) и длины содержимого документа.
- Защитные заголовки `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Cache-Control: no-store`.
- Ответ `401` содержит `WWW-Authenticate: Bearer`; необработанные исключения
  не раскрывают трассировку и SQL.
- Секрет не выводится в `repr` настроек.

## [1.0.0] — исходное состояние

Исходная версия учебного репозитория. Результаты обследования —
[`docs/audit/BASELINE_AUDIT.md`](docs/audit/BASELINE_AUDIT.md).
