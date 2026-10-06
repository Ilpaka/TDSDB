# Document Center API

Внутренний REST API ИП «Северный Контур» для ведения проектной документации:
пользователи и роли, проекты, доступ участников, документы с жизненным циклом
`draft → published → archived`, автоматические версии и журнал действий.

| | |
|---|---|
| Версия приложения | `2.0.0` (SemVer) |
| Версия контракта | `v1`, базовый путь **`/api/v1`** |
| Стек | Python 3.12, FastAPI, SQLModel, SQLite, JWT (HS256), bcrypt |
| Контракт | [`docs/openapi/openapi.json`](docs/openapi/openapi.json) |

## Структура проекта

```text
app/
  main.py            создание приложения, middleware, подключение роутеров
  core/              конфигурация, JWT, роли, права на объекты,
                     ошибки RFC 9457, rate limiting, защитные заголовки
  db/                подключение к базе данных
  models/            SQLModel-модели хранилища
  schemas/           Pydantic-схемы публичного контракта
  services/          бизнес-логика и object-level authorization
  routers/           HTTP-операции /api/v1
scripts/
  create_admin.py    создание первого администратора
  export_openapi.py  экспорт docs/openapi/openapi.json
tests/               контрактные тесты и тесты безопасности (pytest)
frontend/            статический клиент
docs/
  standards/         API_STANDARD, SECURITY_STANDARD, DOCUMENTATION_STANDARD
  audit/             BASELINE_AUDIT, ENDPOINT_INVENTORY, OWASP_API_AUDIT,
                     CERTIFICATION_REPORT
  openapi/           экспортированный контракт
  evidence/          скриншоты-доказательства
  source/            исходники Sphinx
```

## Требования

- Python **3.12** (проверено на 3.12.12; поддерживается 3.11+)
- `pip`, `venv`

## Установка

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # только приложение
pip install -r requirements-dev.txt -r requirements-docs.txt   # + тесты и Sphinx
```

## Настройка `.env`

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # вставьте в JWT_SECRET
```

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `JWT_SECRET` | демонстрационный | Секрет подписи токенов. **В production обязателен, ≥ 32 символов** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Срок действия токена, 1…1440 |
| `DATABASE_URL` | `sqlite:///./app.db` | Строка подключения к БД |
| `CORS_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Разрешённые origin через запятую; `*` в production запрещён |
| `DEBUG` | `false` | В production запрещён |
| `DOCS_ENABLED` | `true` | Публикация `/docs`, `/redoc`, `/openapi.json` |
| `LOGIN_RATE_LIMIT` / `LOGIN_RATE_WINDOW_SECONDS` | `10` / `60` | Лимит попыток входа с одного адреса |
| `MAX_REQUEST_BODY_BYTES` | `1048576` | Максимальный размер тела запроса |

При `ENVIRONMENT=production` приложение **не запустится** с демонстрационным или
коротким секретом, с `DEBUG=true` или с `*` в `CORS_ORIGINS`.

## Первый администратор

Публичной регистрации нет — пользователей создаёт администратор. Первого
администратора создайте локально (пароль не передаётся аргументом командной строки):

```bash
python -m scripts.create_admin --email admin@example.com
```

## Запуск

```bash
uvicorn app.main:app --reload
```

| Адрес | Назначение |
|---|---|
| <http://localhost:8000/docs> | Swagger UI |
| <http://localhost:8000/redoc> | ReDoc |
| <http://localhost:8000/openapi.json> | OpenAPI-схема |
| <http://localhost:8000/health> | Проверка работоспособности |
| <http://localhost:8000/api/v1> | Базовый путь бизнес-операций |

## Получение Bearer-токена

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "<пароль>"}'
# {"access_token": "eyJhbGciOi...", "token_type": "bearer"}

TOKEN=eyJhbGciOi...
curl -s http://localhost:8000/api/v1/projects -H "Authorization: Bearer $TOKEN"
# {"items": [], "total": 0, "offset": 0, "limit": 20}
```

В Swagger UI нажмите **Authorize** и вставьте значение `access_token`.

## Контракт в двух словах

- Коллекции: `?offset=0&limit=20`, `limit` ≤ 100; ответ `{items, total, offset, limit}`.
- Коды: `200` чтение/изменение, `201` создание, `204` удаление без тела;
  ошибки `401/403/404/409/413/422/429`.
- Ошибки — RFC 9457 Problem Details (`application/problem+json`).
- Даты — RFC 3339 UTC: `2026-09-09T08:15:30Z`.
- Публикация и архивирование документа: `PATCH /api/v1/documents/{id}` с `{"status": "published"}`.

Подробно — [`docs/standards/API_STANDARD.md`](docs/standards/API_STANDARD.md).

## Тесты

```bash
pytest
```

Набор проверяет OpenAPI-контракт, HTTP-контракт и безопасность (401/403/404,
BOLA, роли, rate limiting, CORS, production-настройки). Тесты используют
временную базу данных и не затрагивают `app.db`.

## Экспорт OpenAPI

```bash
python -m scripts.export_openapi
```

Файл `docs/openapi/openapi.json` обновляется при каждом изменении контракта;
тест `test_exported_schema_matches_application` упадёт, если его забыли обновить.

## Документация Sphinx

```bash
sphinx-build -W -b html docs/source docs/build/html
open docs/build/html/index.html
```

## Документы

| Документ | Содержание |
|---|---|
| [`docs/standards/API_STANDARD.md`](docs/standards/API_STANDARD.md) | Стандарт REST API v1 |
| [`docs/standards/SECURITY_STANDARD.md`](docs/standards/SECURITY_STANDARD.md) | Стандарт безопасности |
| [`docs/standards/DOCUMENTATION_STANDARD.md`](docs/standards/DOCUMENTATION_STANDARD.md) | Стандарт документирования |
| [`docs/audit/BASELINE_AUDIT.md`](docs/audit/BASELINE_AUDIT.md) | Аудит до исправлений |
| [`docs/audit/ENDPOINT_INVENTORY.md`](docs/audit/ENDPOINT_INVENTORY.md) | Инвентаризация endpoint |
| [`docs/audit/OWASP_API_AUDIT.md`](docs/audit/OWASP_API_AUDIT.md) | Аудит по OWASP API Security Top 10 |
| [`docs/audit/CERTIFICATION_REPORT.md`](docs/audit/CERTIFICATION_REPORT.md) | Итоговое заключение о соответствии |
| [`SECURITY.md`](SECURITY.md) | Политика безопасности |
| [`CHANGELOG.md`](CHANGELOG.md) | История изменений |
