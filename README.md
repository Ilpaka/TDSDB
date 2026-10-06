# TDSDB

Домашние и проверочные работы по дисциплинам курса.

- `MongoDB/` — инфраструктура: `docker-compose.yml`, `Makefile`, init-скрипт для загрузки данных при старте.
- `lesson-01/` — каталог серверов в аренду: документы, запросы, разбор дублирования.
- `api-standardization/` — проверочная работа «Audit API»: стандартизация и оценка соответствия REST API (FastAPI, OpenAPI, OWASP API Top 10). Итоговое заключение — [`CERTIFICATION_REPORT.md`](api-standardization/docs/audit/CERTIFICATION_REPORT.md).
- `Algo_difficult/` — домашние работы по алгоритмизации. `lesson-01/` — замеры времени и памяти алгоритмов в Python ([отчёт](Algo_difficult/lesson-01/README.md)).

```bash
cd MongoDB && make up
```

Compass: `mongodb://root:root@localhost:27017/?authSource=admin`
