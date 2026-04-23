# Локальный запуск

## Предварительные условия

- Docker и Docker Compose
- Для NL-функций: ключ LLM в корневом `.env` (см. `LLM_API_KEY` в [`.example.env`](../../.example.env))

## Команда

Из корня проекта (где лежит `docker-compose.yml`):

```bash
docker compose up --build
```

Дождитесь успешного завершения `main-db-bootstrap` и healthy-проверок БД и RabbitMQ.

## Типичные URL

| Компонент | URL / порт |
|-----------|------------|
| BFF (напрямую) | `http://localhost:8000` |
| Auth | `http://localhost:8002` |
| Analytics | `http://localhost:8009` |
| Report tasks | `http://localhost:8010` |
| Notifications | `http://localhost:8007` |
| RabbitMQ UI | `http://localhost:15672` |
| Frontend (Vite) | `http://localhost:5173` |
| Nginx | `http://localhost:80` |

## Переменные окружения

Скопируйте [`.example.env`](../../.example.env) в `.env` в том же каталоге и заполните секреты. Для фронтенда при необходимости — [`frontend/.env.example`](../../frontend/.env.example) → `frontend/.env`.

## Документация API

- BFF Swagger: `http://localhost:8000/docs` (агрегирует проксируемые контракты).
