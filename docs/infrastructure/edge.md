# Край сети и вспомогательные сервисы

## Nginx

- **Контейнер:** `nginx`
- **Порт:** `80` на хосте
- **Конфиг:** [`infrastructure/nginx/default.conf`](../../infrastructure/nginx/default.conf) (проксирование на BFF и статику по мере настройки).

Фронтенд в dev часто открывают напрямую на `5173`; через nginx — единая точка для демо и CloudPub.

## Redis

- **Контейнер:** `redis`
- **Порт:** `6379`
- **Использование:** BFF — rate limiting при заданном `REDIS_URL` и `RATE_LIMIT_PER_MINUTE` (см. [../bff-service/README.md](../bff-service/README.md)).

## CloudPub

- **Сервис:** `cloudpub` в compose
- **Назначение:** публикация локального `http://host.docker.internal:80` наружу по токену `CLOUDPUB_TOKEN`.
- **Зависимость:** стартует после `nginx`.
