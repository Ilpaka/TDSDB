# CERTIFICATION REPORT — Document Center API

Внутреннее заключение о соответствии API установленным стандартам
(предсертификационный отчёт). Документ **не является внешним сертификатом**:
OpenAPI, Swagger, ReDoc и Sphinx служат средствами описания контракта, а
OWASP API Security Top 10 — базой для аудита рисков.

---

## 1. Объект оценки

| Параметр | Значение |
|---|---|
| Объект | Document Center API — внутренний REST API ИП «Северный Контур» (FastAPI) |
| Исходный репозиторий | [MaximBytecamp/tz-severn-kontur-fastapi](https://github.com/MaximBytecamp/tz-severn-kontur-fastapi) |
| Рабочий репозиторий | Fork `Ilpaka/tz-severn-kontur-fastapi`, ветка `feature/api-v1-standardization`; комплект сдачи — [Ilpaka/TDSDB](https://github.com/Ilpaka/TDSDB/tree/api-standardization/api-standardization), каталог `api-standardization/` |
| Commit baseline | `ccc390a` |
| Commit оценки | `fa8314b` (последний commit кода и тестов перед выпуском отчёта) |
| Версия приложения | `2.0.0` (до оценки — `1.0.0`) |
| Версия контракта | `v1`, базовый путь `/api/v1` |
| Дата оценки | 2026-09-09 |
| Issue | [Ilpaka/TDSDB#2](https://github.com/Ilpaka/TDSDB/issues/2) |
| Pull Request | [Ilpaka/TDSDB#3](https://github.com/Ilpaka/TDSDB/pull/3) |

## 2. Область оценки

| Область | Что проверено |
|---|---|
| Endpoint | Все 24 операции контракта: 22 бизнес-операции `/api/v1` и служебные `/`, `/health` (перечень — `docs/openapi/openapi.json`) |
| HTTP-контракт | Методы, коды успеха и ошибок, `Content-Type`, заголовки `WWW-Authenticate`, `Retry-After` |
| Данные | Типы и имена полей, даты, enum, ограничения, отсутствие служебных полей в ответах |
| Коллекции | Пагинация, конверт ответа, ограничения `limit` |
| Ошибки | Структура Problem Details, реестр типов, отсутствие внутренних деталей |
| Безопасность | JWT, роли, object-level authorization, CORS, секреты, production-настройки, ресурсные ограничения |
| OpenAPI / Swagger / ReDoc | Полнота описания операций, схем, примеров и security |
| Документация | Docstrings, Sphinx, README, SECURITY, CHANGELOG, стандарты, аудит |
| Git-процесс | Issue, ветка, история коммитов, Pull Request |

Вне области: frontend (`frontend/`) — проверено только обращение к базовому
пути `/api/v1`; инфраструктура развёртывания (TLS, обратный прокси).

## 3. Критерии

| Документ | Назначение |
|---|---|
| [`docs/standards/API_STANDARD.md`](../standards/API_STANDARD.md) | Правила STD-VER, STD-URI, STD-HTTP, STD-DATA, STD-COL, STD-ERR, STD-DOC, STD-SEC |
| [`docs/standards/SECURITY_STANDARD.md`](../standards/SECURITY_STANDARD.md) | Правила SEC-AUTH, SEC-ROLE, SEC-OBJ, SEC-CFG, SEC-RL, SEC-EXT |
| [`docs/standards/DOCUMENTATION_STANDARD.md`](../standards/DOCUMENTATION_STANDARD.md) | Правила DOC-PY, DOC-API, DOC-SPX, DOC-REPO, DOC-GIT |
| RFC 9110, RFC 9457, RFC 3339, RFC 6750 | HTTP-семантика, ошибки, даты, Bearer |
| OpenAPI Specification 3.1 | Формальное описание контракта |
| OWASP API Security Top 10 (2023) | Аудит рисков — [`OWASP_API_AUDIT.md`](OWASP_API_AUDIT.md) |

## 4. Метод

1. **Ручной аудит исходного состояния** — `BASELINE_AUDIT.md`, `ENDPOINT_INVENTORY.md` (до изменения кода).
2. **Code review** — `app/`, `scripts/`: обход маршрутов, сервисов, зависимостей и конфигурации; AST-проверка наличия docstrings у публичных имён.
3. **Инспекция OpenAPI** — экспортированный `docs/openapi/openapi.json`, просмотр в Swagger UI и ReDoc.
4. **Автоматические тесты** — 93 проверки `pytest` (`tests/test_openapi_contract.py`, `tests/test_http_contract.py`, `tests/test_security_contract.py`) на временной базе данных.
5. **Ручные запросы** — запуск `uvicorn` на демо-базе, вызовы через Swagger UI и `curl`.
6. **Сборка документации** — `sphinx-build -W` (предупреждения как ошибки).

## 5. Исходные несоответствия

По `BASELINE_AUDIT.md` (commit `ccc390a`): **0 PASS / 10 FAIL**.

| ID | Критерий | Ключевое несоответствие |
|---|---|---|
| A-01 | Единая версия API | Префикс версии отсутствовал |
| A-02 | Единообразие URI | Смешение `/projects` и `/projects/`; глаголы `grant`, `publish`, `archive`, `restore` |
| A-03 | HTTP-методы | Изменение состояния через `POST` на глагольный URI; нет `DELETE` для проектов и документов |
| A-04 | Status codes | Явный код у 5 из 21 операции; ошибки не объявлены |
| A-05 | Формат ошибок | Два формата `{"detail": ...}`; RFC 9457 не применялся |
| A-06 | Полнота OpenAPI | Нет `summary`, `description`, `operationId`, `responses` |
| A-07 | Security scheme | `require_admin` возвращал `False` — журнал аудита был открыт всем (OWASP API5) |
| A-08 | Production-defaults | Рабочий `JWT_SECRET` по умолчанию |
| A-09 | CORS | `*` вместе с `allow_credentials=True` |
| A-10 | Документация | Пустой README; нет SECURITY, CHANGELOG, Sphinx, стандартов, контракта |

Дополнительно зафиксированы дефекты D-01…D-10 (неработающий `/audit`,
некомпилируемое регулярное выражение пароля, `skip` вместо `offset`,
`limit` до 500, отсутствие тестов и др.).

## 6. Исправления

### 6.1. Результат по критериям baseline

| ID | Итог | Что изменено | Где | Доказательство |
|---|---|---|---|---|
| A-01 | **PASS** | Все бизнес-роутеры под `settings.API_V1_PREFIX` = `/api/v1`; вне версии — `/`, `/health`, `/docs`, `/redoc`, `/openapi.json` | `app/main.py:setup_routers` | `test_business_paths_start_with_api_v1` |
| A-02 | **PASS** | Единый стиль без слэша; глагольные URI заменены операциями над ресурсами | `app/routers/*` | `test_no_trailing_slash_and_no_mixed_style`, `test_paths_are_lowercase_without_verbs`, `test_trailing_slash_is_not_an_alias` |
| A-03 | **PASS** | `PATCH status` вместо `publish/archive`; `PUT .../access/{user_id}`; `POST .../versions` для восстановления; добавлены `DELETE` | `app/routers/documents.py`, `access.py`, `projects.py` | `test_patch_returns_200_*`, `test_put_access_returns_201_then_200`, `test_delete_returns_204_without_body` |
| A-04 | **PASS** | Явный `status_code` и `responses` у каждой операции; 204 без тела | все роутеры, `problem_responses` | `test_every_operation_documents_success_response`, `test_protected_operations_declare_security` |
| A-05 | **PASS** | RFC 9457 Problem Details через централизованные обработчики; реестр типов; `errors` для 422 | `app/core/problems.py`, `app/schemas/problem.py` | `assert_problem` в 40+ тестах, `test_validation_error_lists_fields`, `test_error_body_has_no_internal_details` |
| A-06 | **PASS** | Теги с описаниями, `summary`, `description`, стабильные `operation_id`, `response_description`, примеры ошибок по типам; восстановлены типы полей в схемах ответа | все роутеры, `app/schemas/base.py:UTCDateTime` | `test_every_operation_has_tag_summary_and_description`, `test_operation_ids_are_unique`, `test_schema_properties_have_types`, `test_parameters_are_described` |
| A-07 | **PASS** | `require_roles` возбуждает 403; роль в описании каждой операции; Bearer в `securitySchemes` и `security` | `app/core/deps.py`, `app/core/security.py` | `test_non_admin_cannot_read_audit_log`, `test_bearer_security_scheme_declared`, `test_protected_operations_state_required_access` |
| A-08 | **PASS** | В production блокируются демо- и короткий секрет, `DEBUG=true`; секрет скрыт в `repr` | `app/core/config.py:_validate_production_safety` | `test_production_rejects_unsafe_configuration` (4 случая), `test_production_accepts_safe_configuration` |
| A-09 | **PASS** | CORS по `CORS_ORIGINS`, `*` в production запрещён, ограничены методы и заголовки | `app/main.py:setup_cors_middleware` | `test_cors_allows_only_configured_origins` |
| A-10 | **PASS** | README, SECURITY, CHANGELOG, три стандарта, Sphinx, OpenAPI-контракт, аудит | корень, `docs/` | Раздел 8; `docs/evidence/03_sphinx.png` |

**Итог после исправлений: 10 PASS / 0 FAIL.**

### 6.2. Дополнительные изменения, выявленные в ходе оценки

| Изменение | Основание | Commit |
|---|---|---|
| Ограничение попыток входа (429 + `Retry-After`), лимит тела 1 МиБ (413), лимит длины содержимого документа, защитные заголовки | STD-SEC-09, OWASP API4, API8 | `846a062` |
| Скрипт `scripts/create_admin.py`: без него пустая база не позволяла получить первого администратора, т. к. публичная регистрация упразднена | SEC-AUTH-08 | `a53d3b3` |
| Регистрация всех ORM-моделей в `app.models` — `create_db_and_tables` зависел от порядка импорта роутеров | Работоспособность | `af7e178` |
| Исправлен `field_serializer("*")` в `APISchema`: все поля схем ответа теряли тип в OpenAPI (`"id": "string"` в Swagger) | STD-DOC-05, STD-DATA-02 | `be8bc45` |
| Docstring роутеров обрезается перед `Args:` — внутренние параметры не попадают в Swagger | STD-DOC-03 | `be8bc45` |
| Ошибки с одинаковым кодом больше не затирают друг друга в `responses`; пример для каждого типа | STD-DOC-07, STD-DOC-09 | `57fb434` |
| Роль или уровень доступа указаны в описании всех 22 защищённых операций | STD-SEC-04 | `ece0f20` |
| Явный `null` для обязательных полей в `PATCH` давал `500`; теперь `422`, `null` для необязательных полей очищает значение | STD-DATA-08 | `6297663` |

### 6.3. Сводка по группам правил

| Группа | Правил ОБЯЗАТЕЛЬНО | Выполнено | Способ подтверждения |
|---|---|---|---|
| STD-VER (версионирование) | 5 | 5 | Тесты, `versioning.rst`, `CHANGELOG.md` |
| STD-URI | 7 | 7 | `test_openapi_contract.py` |
| STD-HTTP | 6 | 6 | `test_http_contract.py` |
| STD-DATA | 8 | 8 | `test_http_contract.py`, `test_patch_null_*`, `test_schema_properties_have_types` |
| STD-COL | 7 | 7 | `test_pagination_*`, `test_collection_envelope` |
| STD-ERR | 9 | 9 | `assert_problem`, `test_error_*` |
| STD-DOC | 11 | 11 | `test_openapi_contract.py` |
| STD-SEC | 9 | 9 | `test_security_contract.py` |
| SEC-* (SECURITY_STANDARD) | 32 | 32 | `test_security_contract.py`, `OWASP_API_AUDIT.md` |
| DOC-* (DOCUMENTATION_STANDARD) | 26 | 26 | AST-проверка docstrings, `sphinx-build -W`, ручной чек-лист |

## 7. Остаточные несоответствия

Отклонений от правил уровня **ОБЯЗАТЕЛЬНО** не выявлено. Ниже — правила уровня
РЕКОМЕНДУЕТСЯ, не реализованные с обоснованием, и принятые остаточные риски.

| № | Правило / риск | Уровень | Обоснование | Планируемое действие |
|---|---|---|---|---|
| R-01 | STD-COL-08 — параметр сортировки `sort` | РЕКОМЕНДУЕТСЯ | Коллекции имеют фиксированный документированный порядок (журнал — по убыванию времени); клиентам v1 сортировка не требуется | Добавить `sort` как совместимое изменение в `2.1.0` |
| R-02 | SEC-AUTH-10 — отзыв выданного токена | РЕКОМЕНДУЕТСЯ | Компенсируется сроком жизни 60 минут и проверкой `is_active` и роли по БД при каждом запросе | Refresh-токены и список отзыва |
| R-03 | SEC-RL-05 — общий rate limiting всех операций | РЕКОМЕНДУЕТСЯ | Ограничен единственный публичный поток (вход); ограничитель хранит состояние в памяти одного процесса | При нескольких репликах — Redis и лимиты на обратном прокси |
| R-04 | SEC-CFG-07 — `/docs` в production | ДОПУСКАЕТСЯ | API внутренний; отключается `DOCS_ENABLED=false` | Отключать при публикации во внешнюю сеть |
| R-05 | DOC-SPX-06 — сборка Sphinx с `-W` | РЕКОМЕНДУЕТСЯ | Выполнено: сборка проходит с `-W` | — |
| R-06 | Ответы с ошибками объявлены в OpenAPI под `application/json` и `application/problem+json` | Замечание | Ограничение FastAPI: `model` в `responses` всегда добавляет `application/json`. Фактически сервер отдаёт `application/problem+json` (проверено тестами) | Принято |
| R-07 | HSTS и TLS | Вне области | Настраиваются на обратном прокси | Описать в руководстве по развёртыванию |
| R-08 | Frontend (`frontend/app.js`) не содержит функций `showMainInterface`, `loadProjects` — унаследовано из исходного репозитория | Вне области | Объект оценки — API; базовый путь клиента переведён на `/api/v1` | Отдельная задача по клиенту |

## 8. Доказательства

| Доказательство | Расположение |
|---|---|
| Экспортированный контракт | [`docs/openapi/openapi.json`](../openapi/openapi.json) — `python -m scripts.export_openapi`; актуальность проверяет `test_exported_schema_matches_application` |
| Тесты | `tests/` — **93 passed** (`pytest`), скриншот [`04_tests.png`](../evidence/04_tests.png) |
| Swagger UI | [`01_swagger.png`](../evidence/01_swagger.png) — раскрытая операция `GET /api/v1/projects/{project_id}`, выполненный запрос с ответом 200 и защитными заголовками (токен на снимке скрыт) |
| ReDoc | [`02_redoc.png`](../evidence/02_redoc.png) — title и версия `2.0.0`; [`02_redoc_schemas.png`](../evidence/02_redoc_schemas.png) — схема ответа с типами полей |
| Sphinx | [`03_sphinx.png`](../evidence/03_sphinx.png) — `sphinx-build -W -b html docs/source docs/build/html` без предупреждений |
| Pull Request | [`05_pull_request.png`](../evidence/05_pull_request.png), [Ilpaka/TDSDB#3](https://github.com/Ilpaka/TDSDB/pull/3) |
| Issue | [Ilpaka/TDSDB#2](https://github.com/Ilpaka/TDSDB/issues/2) |
| Аудит | [`BASELINE_AUDIT.md`](BASELINE_AUDIT.md), [`ENDPOINT_INVENTORY.md`](ENDPOINT_INVENTORY.md), [`OWASP_API_AUDIT.md`](OWASP_API_AUDIT.md) |
| История изменений | Серия коммитов от `ccc390a` в формате Conventional Commits (`git log ccc390a..HEAD`); [`CHANGELOG.md`](../../CHANGELOG.md) |

## 9. Итог

**CONFORM**

Document Center API версии `2.0.0` (контракт `/api/v1`) соответствует
`API_STANDARD`, `SECURITY_STANDARD` и `DOCUMENTATION_STANDARD` версии 1.0.0:
все правила уровня ОБЯЗАТЕЛЬНО выполнены и подтверждены автоматическими
тестами, инспекцией контракта или документами; все 10 критериев baseline
переведены из FAIL в PASS; применимые категории OWASP API Security Top 10
(8 из 10) получили статус PASS.

Заключение действительно для commit `fa8314b` и последующих коммитов, не
изменяющих код `app/`. Остаточные риски R-01…R-08 не влияют на соответствие
и учитываются при развитии API. При развёртывании в нескольких репликах
необходимо выполнить действие по R-03.
