# Доска заявок ИТ-отдела

Учебная доска после главы 2.5. Студент указывает кабинет, категорию и описание проблемы. Дежурный принимает заявку, меняет её статус и убирает готовую карточку. Заявки хранятся в коллекции `requests` в PocketBase. Открытая доска получает изменения по подписке.

## Запуск

Из корня репозитория под Node.js 24 и с запущенным Docker выполните:

```bash
cd React/avtomatizaciya
docker compose up -d --build pocketbase
cd ../zayavki
npm ci
npm run dev
```

Откройте `http://localhost:5173`. При первом запуске базы появятся пять примеров. Откройте второе окно, добавьте заявку и проверьте, что карточка появилась в обоих окнах. Для проверки ошибки остановите PocketBase, обновите страницу, затем запустите базу и нажмите «Повторить».

Для этой доски уведомления принимает вебхук `/webhook/zayavka` из первого модуля. Его можно подключить отдельно. При недоступном n8n заявка сохранится в PocketBase. Для сборки выполните `npm run build`, для проверки кода — `npm run lint`.

[Версия доски после главы 1.7](https://github.com/Ilpaka/TDSDB/tree/6f65b101da85ce37aa1bb6c3b2ecdde0ece5da68/React/zayavki) · [Глава 2.5](https://maximbytecamp.github.io/angular_react_makarov/temy/25-obnovlenie-po-sobytiyam/index.html) · [Проект общежития с базой](../projects/p2-obshchezhitie/README.md).
