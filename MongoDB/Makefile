.PHONY: up down restart reseed logs ps shell clean

up:
	docker compose up -d

down:
	docker compose down

restart: down up

# Снести данные и заново залить seed.json
reseed: clean up

logs:
	docker compose logs -f mongo

ps:
	docker compose ps

shell:
	docker compose exec mongo mongosh -u $${MONGO_USER:-root} -p $${MONGO_PASSWORD:-root}

clean:
	docker compose down -v
