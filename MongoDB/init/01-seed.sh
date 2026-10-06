#!/bin/bash
# Выполняется образом mongo один раз — при первом старте с пустым volume.
# Заливает каталог серверов из lesson-01/seed.json (смонтирован в /seed).
set -e

mongoimport \
  --username "$MONGO_INITDB_ROOT_USERNAME" \
  --password "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --db hosting \
  --collection servers \
  --jsonArray \
  --file /seed/servers.json
