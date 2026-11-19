# Angular и React

Работы по дисциплине за 2026/2027 учебный год. Каждое приложение запускается из своей папки.

| Работа модуля 1 | Папка |
|---|---|
| Доска заявок по главам 1.1–1.7 | [Версия после главы 1.7](https://github.com/Ilpaka/TDSDB/tree/6f65b101da85ce37aa1bb6c3b2ecdde0ece5da68/React/zayavki) |
| Проект «Заявки в общежитие» | [projects/p1-obshchezhitie/](projects/p1-obshchezhitie/README.md) |
| Уведомления о заявках в Telegram | [avtomatizaciya/](avtomatizaciya/README.md) |

| Работа модуля 2 | Папка |
|---|---|
| Доска ИТ-отдела по главам 2.1–2.5 | [Версия после главы 2.5](https://github.com/Ilpaka/TDSDB/tree/a608c57236277a3a51dd03ffa2aad1d2b4489bf9/React/zayavki) |
| Общежитие с общей базой PocketBase | [projects/p2-obshchezhitie/](projects/p2-obshchezhitie/README.md) |
| ИИ-диспетчер и кнопка «Взять» | [Два процесса n8n](projects/p2-obshchezhitie/n8n/) |

| Работа модуля 3 | Где открыть |
|---|---|
| Маршруты и контекст доски ИТ-отдела | [zayavki/](zayavki/README.md) |
| Мониторинг сайтов и ночные оповещения | [Отчёт и журнал](projects/p3-monitoring/README.md) · [Опубликованный сайт](https://ilpaka.github.io/monitoring/) |

| Работа модуля 4 | Где открыть |
|---|---|
| Дайджест новостей и два процесса n8n | [Отчёт и журнал](projects/p4-digest/README.md) · [Дайджест на GitHub Pages](https://ilpaka.github.io/digest/) |

[Справочник курса](https://maximbytecamp.github.io/angular_react_makarov/) · [Правила сдачи](https://github.com/MaximBytecamp/react-kurs-template/blob/main/docs/SUBMIT.md)

## Где посмотреть код из глав

| Главы | Что открыть |
|---|---|
| 1.1–1.7 | [Доска с компонентами, формой и сохранением в браузере](https://github.com/Ilpaka/TDSDB/tree/6f65b101da85ce37aa1bb6c3b2ecdde0ece5da68/React/zayavki/src) |
| 2.1 | [Таймер и заголовок вкладки](zayavki/src/BoardProvider.tsx) · [сброс фильтра по Esc](zayavki/src/pages/BoardPage.tsx) |
| 2.2–2.3 | [Коллекции и правила PocketBase](avtomatizaciya/pocketbase/pb_migrations/1795046400_request_boards.js) · [запросы к базе](zayavki/src/api.ts) |
| 2.4–2.5 | [Хук загрузки и изменения списка](zayavki/src/useRequests.ts) · [подписка на события](zayavki/src/realtime.ts) |
| 3.1–3.2 | [Маршруты](zayavki/src/App.tsx) · [общие данные страниц](zayavki/src/BoardProvider.tsx) |
| 3.3–3.4 | [Публикация и ночная проверка сайтов группы](https://github.com/Ilpaka/monitoring/tree/main/.github/workflows) |
| 4.1–4.3 | [Тесты, доступность и фильтры монитора](https://github.com/Ilpaka/monitoring) · [журнал задания агенту](https://github.com/Ilpaka/monitoring/blob/main/ai-log.md) |
| 4.4 | [Та же страница на Angular и четыре теста](monitoring-ng/README.md) |
