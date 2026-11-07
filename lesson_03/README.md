# Практика 01 · Каталог товаров

Илья Панов · [отчёт по шаблону](homework_03.md) · [решение](solution.py) · [результат проверки](check-result.txt).

Исходные данные из [mongodb-practice](https://github.com/MaximBytecamp/mongodb-practice) включены для воспроизводимости: `shop.products`, `sandbox.products` и `logs.events`. Стенд изолирован на `127.0.0.1:27037`, чтобы не затрагивать другие базы.

## Запуск из корня репозитория

Нужны Docker с Compose и Python 3.10+.

```bash
docker compose -f lesson_03/compose.yaml up -d --wait
python3 -m venv .venv
. .venv/bin/activate
pip install -r lesson_03/requirements.txt
python lesson_03/reset.py
python lesson_03/solution.py
MONGO_URI=mongodb://localhost:27037 python lesson_03/check.py
python lesson_04/capture.py
```

`reset.py` **удаляет и заново загружает** только три учебные коллекции на указанном сервере. Используйте изолированный стенд. Скрипт планов удаляет вторичные индексы в `logs.events` и оставляет индекс второго запроса. Команда завершения стенда: `docker compose -f lesson_03/compose.yaml down`.

Для просмотра данных и сохранённого вывода в браузере после выполнения команд запустите `python lesson_03/view.py` и откройте `http://127.0.0.1:8767`.

Для каждого нового испытания приёмки сначала выполните `reset.py`: повторный запуск `solution.py` повторно увеличивает остатки, хотя новые товары с теми же `_id` не дублируются.
