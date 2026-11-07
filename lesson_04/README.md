# Домашнее задание № 4 · План запроса и индексы

Илья Панов · 07.11.2026 · MongoDB 8.0.34, `logs.events`, 1200 исходных событий. Планы получены через `explain` с `executionStats`; шаги ниже перечислены от источника к результату.

## Сводная таблица

| План | Индекс | Возвращено | Документов | Ключей | Шаги |
|---|---|---:|---:|---:|---|
| [1](plan-1.json) | нет | 33 | 1200 | 0 | COLLSCAN → SORT |
| [2](plan-2.json) | service, level, ts, duration_ms | 33 | 33 | 43 | IXSCAN → FETCH |
| [3a](plan-3a.json) | duration_ms, service, level, ts | 33 | 33 | 378 | IXSCAN → SORT → FETCH |
| [3b](plan-3b.json) | service, level, duration_ms, ts | 33 | 33 | 33 | IXSCAN → SORT → FETCH |
| [4 без индекса](plan-4-bez.json) | нет | 10 | 1200 | 0 | COLLSCAN → SORT |
| [4 с индексом](plan-4.json) | level, duration_ms | 10 | 10 | 10 | IXSCAN → FETCH → LIMIT |

Числа — результаты конкретных запусков, а не обещание времени ответа. Чтобы повторить, используйте [инструкцию стенда](../lesson_03/README.md); [capture.py](capture.py) последовательно меняет индексы и сохраняет шесть планов. Индексы тестируются отдельно, только `_id_` остаётся всегда.

## Задача 1. До индекса

```javascript
db.events.find({service: "payments", level: "error", duration_ms: {$gt: 500}}).sort({ts: -1})
```

Без подходящего индекса сервер перебрал все 1200 документов и только затем выбрал 33 подходящих; найденные документы пришлось сортировать отдельным шагом. Ключи индекса не использовались. [Открыть разбор плана](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:zVbbbuM2EP0XYh_dQLIuvrzZstUGjetslO5isSgKWhrLbChSS1KOvYb_vUPKt2S7SbAFij7Z5pwZHs6Zi3cENjWnTHwApZkUZEh80iFfGlDbW06FAEWGOyJoBbqmOaCdy1JfwRqE0YisqdJQvLd4C3xHRUGGn3eEI4K7E_iCTqCUVGS_7-yIBrVmNtLRVtNt5aI5c9EoapDJn5V2kNKQYeR5-_0f-w5hooBNyrgBlQEalpRrOND9heoVRot6QTdIxrHlhg9IaL6CbEVreMH-KyB54vXTsZ-MrEXWhlXsqyNyzyqYMc4Z8vE6pKKba8sCirnKJG8sRN-BDVOcCJ1BI1G8hMpyKvS9nKIIsoDngFo1AooMqXCq2oD6ZHxkQjBRWpVsophOnjprQ0urVza_u8cnaanMLTWYOQfHdA9_8jGlFVQ3eAEm0_fCftSLPXyk2dbWVbOq5kBs3uvGZG3A3SlyMr-5yZLRbwhYOk3-gwoomILctJW6lOqRqsJ6EQV_4TkUNh3o9tliMV25yzwyNy7W-aTJc9B4ZlSDuRJ3YBolbPaC4MLxmfZGGsqxWPR0Qyvm4MfTicwvTv2uzeLl_SXot6j0OpGpxtKkBtzVj1I9aHtdEHUILdZU5EdXAVBYL0fGb39_YsBbzpquwWalDaNAG6kuDvCaeYqe_7Js2sxQQzP2FTKMZMkN_D7GbXBqTJh-OCeixue1aXZf0WwdkRcmyPq3xP43hfijSlktvquUH_d-WKl_6gw8_aYubbdQzl2jTI-sDx3jBunltByNBtM08v3I97wkCCaDYDQYJVHY70ZhMoiDfhR5aZhMg8k49Cf-JPanUYyoNAyCJA0nyCCXVeWk2KE49pOclsdZrJMSZwk6R-EOinW-r0dbpk_q812xOOwqYs0YHnCCLqUFraRGMOkvu4sw7NJFN-zZbeBCdHuejxqsT-uwf-VdBSHaS2bOSzLyi0UY-RGNo0GPQpEvY7_fBwgh7NNuD-Jo4cURhfPlt1ThEsXntnNA2I6i3C3OFBerGTfLJW41LPTx1thhcdFX36JndDNvDPYCzp2XfW6kfGhq1zLX9qiCgmHxoF9j84yBXvY_AjPZqBx-VrKp0WcGlVTbV5gibsxl_oBbyjZ_6_O7RiavON4quWILZo7eM1AlzMVMilJmhznw9J5RUdxL_Evw1ncg9CMWo3xMbaPpt74otRraVk6kMEra4jTYMAvc3NooZhcQef6W9l_UdSmwb90O_8jMKpGcu1pOpbqDEjZ4J5aKxHnoX3n7vwE).

## Задача 2. ESR

Equality: `service`, `level`; Sort: `ts` по убыванию; Range: `duration_ms > 500`.

```javascript
db.events.createIndex({service: 1, level: 1, ts: -1, duration_ms: 1})
```

`IXSCAN → FETCH`: 33 возвращено, 33 документа и 43 ключа просмотрено. Просмотр документов снизился с 1200 до 33, то есть примерно в **36,36 раза**. Поле `ts` идёт после равенств, поэтому подходящий участок индекса уже упорядочен и отдельный `SORT` не нужен. 43 ключа больше 33 результатов: при сохранении порядка по `ts` диапазон по последнему полю не образует один узкий непрерывный отрезок; среди проверенных ключей есть неподходящие и служебные переходы. [Открыть разбор плана](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:7VZLc9s2EP4rGUwOPSgeUiT1ukmU2Hhaxa7pNO04Hg1ErCTEJMAAoC1Ho__eBShRj05tH9uZnkjuix92v13shsC6zCkXv4PSXAoyID5pke8VqOfrnAoBigw2RNACdEkzQH0ul_oCHkEYjZYlVRrYb9beGr6ngpHB3YbkaJE7CXxHJ1BKKrLdtjZEg3rkNtJeV9LnwkVzalYpahDJrNDOZGnIIPK87fZ-2yJcMFgnPDegUkDFguYadnA_Ur3CaFE3aAfxqGOx4QFimq0gXdESXtD_AgieJFHfDzu-1cjS8IL_cEBueQFTnucc8XgtUtD1pUUB7EqlMq-sib4BG4Y1gA5GQ8FeskozKvStnGARJINzg1JVAliKUHKq6oC6UT5xIbhY2irZRHEdnzprQ5e2XsnkNv5IbO7KyqS1cNNoL_9I4-EnVD_A8zU1mFgXrSmS39qXEt-wRoMP-Dypkb-vyyckCUbcuc78mXPEp9GzD_7syGlmOcb1tMoNd7nfJ2QnQCArfQLj7r7BYV8tEPs8AXLnGKI_C458aGJynTqOHgmuqTKc5geJRd80QBvDcgWZqdthIdUTVYzszEayEuwMG7n72pD4K2m9O_66J0fIraHrhNpq9-pM3InI3ZSu8fytd1Mu8Ok0p2ckP2EztN5xsbjwUL3FniEKviFcYJYK-zwgVTLHOqy4cXgPkirLQKPMqApPL27AVEpY5gTBkeMZ7400NEdMerKmBXfmYbATj2V2JD6J4gin30TQ14FMNLYlNeAAPUn1oGsQlD1Ske0dBQCzPmTQrz_-5JAz56PpI9iE1BEUaCPVkQD_cJU4prO_nYjmCiizU-Zq_q22frmh_k3H-b-5_5PN7Qp31nAawPLE96xzqW-x6FCzwX6OlSxL920HA81zNxMme-7t8ujuy-NLcTjsT5LI9yPf8-IgGPeDYX8YR2GvHYVxvxP0oshLwngSjEehP_bHHX8SddAqCYMgTsIxJjCTReEu_w1ZcPskzY6wcBf2SVoPl36TwN2O0PrnDQAPL5WxspqrKHjP5ruVhFg1hge8KBfSGq2kRmPSW7TnYdim83bYtZe-C9Huen63RR6brad34V0EIeqX3Bx2ochn8zDyI9qJ-l0KLFt0_F4PIISwR9td6ERzrxNROPwc6YedgsetZ56wPUdztx8luD-ZUbVY4PLCf8Do2YArZNiLuh3PDZRza2TMVWVwzOCEfdnnVykfqtJNo0srKoBxnAPoV9k8Y6CX_feGqaxUBj8rWZXoM4VCqudXkKLdKJfZAy4jKSa39vmsEckrjtdKrvicm733FNQSrsRUiqVMdyP29D9Dxm4lbn5vPQeafkEyyqfEzkz91hMltoZ2IMdSGCUtOQ02zBwXNG0Ut3ctOT9LvSxfLgWOYLeqfeFmFcs8d1xOpLqBJazriSof8Hnhbf8C).

## Задача 3. Порядок полей

В варианте A диапазон расположен первым: MongoDB проходит участок значений `duration_ms > 500`, включая события других сервисов и уровней, поэтому просмотрено 378 ключей. Сортировка по времени остаётся отдельной. В варианте B равенства сначала сужают диапазон до 33 ключей, но `ts` находится после диапазона `duration_ms`: общий порядок по времени внутри него не гарантирован, поэтому нужен `SORT`.

Для этого запроса я бы выбрал ESR-вариант: он читает немного больше ключей, чем B, но не выполняет блокирующую сортировку. В рабочей системе решение зависит от объёма, селективности, `limit`, профиля нагрузки и цены поддержки индекса; стоит измерять оба варианта на репрезентативных данных. При превышении лимита памяти сортировка может использовать диск или завершиться ошибкой — это зависит от версии и настроек MongoDB, поэтому отсутствие `SORT` не следует объяснять безусловным падением.

## Задача 4. Десять самых долгих ошибок

```javascript
db.events.find({level: "error"}).sort({duration_ms: -1}).limit(10)
db.events.createIndex({level: 1, duration_ms: -1})
```

`level` — равенство, `duration_ms` — сортировка; диапазон отсутствует. Без индекса: 10 возвращено, 1200 документов и 0 ключей просмотрено. С индексом: 10 возвращено, 10 документов и 10 ключей просмотрено, `IXSCAN → FETCH → LIMIT`. Хотя ошибок 180, индекс сразу отдаёт их по убыванию длительности, и после первых десяти подходящих документов `limit` останавливает чтение. [Открыть разбор плана](https://dfrancour.dev/tools/mongodb-paste-the-plan#v1:7VZZc9s2EP4rGUweFQ9J85LfdLHRNIpdU2nacTweiFhJiEGAAUBbjsf_vQvosCxPHfd46ENfeGC_xV4fFntPYNUIyuWvoA1XkpyQkHTItxb03ZmgUoImJ_dE0hpMQytAuVALcwQ3IK1BZEO1AfaLwzugQIFwH2_hG2JBa6XJw0OHcMlgVXBhQZdgycmcCgMbQ--pWSI4zYa9PBgWblc0PaDVEsolbeAF-c-AZkkv6KZFmB2jRDWW1_w7tRjMlNcw4UJwQ06CDqnpauy8AHaqSyVaBzHn4LZhO4ceQT3JXkKVFZVmqkaYPsXgENDoVgIr0RVB9XpDsxPecim5XLj8ulRxM3iqbCxduEx_GE_GU4xJ4Da2V6tWYuLCwCWzaW25Rt3v4MVoOnhP_kw6_q0c9D6i-BruzqjFOsi9goUdwlrts3ZVo6fvwm3NPmLpXdUd7iq82kNdvXNU4WbSCst9IbbZ2SygmaXZM3JxeWDl4tJZMZ8kRx7s1LkpPav2Fs6otpyKxxXn2Y6yEW7LNVR2TeC50rdUM7KB9TFv7Ikb5OLLmplfSOfN7vOSPHOPXEzoCgPpvJlwiW-EPDw4Nmv4iuaAuRJu48ASV54tmHrr7T2utFUFBtesbtF7eQ621dJV3FVzBzvgq1WWCrRqRita8x3cLw9VdbC8b34B5lXE-rEjI4PHiVrwDt0qfY0bh0gWym6orLaKEoA5HY9yP79zEMz_GXoDLiFrmQZjld5bQAunhaffXyT533Q9-Nddxy_2rBhUaKDMNbbT2dc1-uVD-V8K5_8G8Y8ahE_gAR8MgK-X02_MFHMP66K436FWTeP_fW-hQvi2MtpyYJMGf1Xu34dFlOZp0k36WTHqF3medrvhMT7DJAi7wTBL0iQrevFxHoVJLxoc58MkTvNuNAoHSRx1XW0qVddUMhf7nLs32V3sc39X72Vle5ljNEpbJ3hOCH-INyHjDSegT2213Pa9t2y2mR_8LqBvAO_GuXJ7LZVBRZLPo1kcR3QWxZm7572lKAvCrENudiNKfhQcHccoX3D7OLgkIZvFSZhQTEpGgVXzNMxzgBjinEYZpMksSBMKj8aRNUheDHPdLqXjPBV-mClw2LH9dj7HeYV_h_6dBX_g4jzJ0sAf6EM0UuG0tXjMsTm_rPNBqeu28d1g7JZqYBzPIeq1NaYfN3pZfwssVasr-EmrtkGdCdRK3_3AU8T1haqusTolJnet88mgJz9QPNNqyWfcbrUnoBdwKidKLlS5aXFP7fQYmyoc9l4bB0I_IwnVbeF6lnltRIWroWuIAyWtVo6pFg_KDGcyYzV31zQ5jGU92Y4XElugn84-c7scKCE8nwulz2EBK7SJVFHX-D4KHv4A).

## Вопросы к защите

- `totalKeysExamined` считает просмотренные записи индекса, `totalDocsExamined` — обращения к документам коллекции. Это разные ресурсы; один показатель не заменяет другой.
- `FETCH` читает полные документы по ссылкам из индекса: запрос возвращает документы целиком, поэтому индекс не покрывает выдачу.
- При вставке события MongoDB должна обновить и подходящие индексы; это увеличивает объём записи и занимаемое место. Для уникального индекса также проверяется уникальность.
- Индексирование всех полей подряд не бесплатно: индексы занимают память и диск, замедляют вставки и обновления, а порядок ключей влияет на применимость и сортировку. Индексы выбирают под реальные запросы и проверяют статистикой.
