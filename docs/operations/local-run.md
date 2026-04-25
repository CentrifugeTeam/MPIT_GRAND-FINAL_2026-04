# Локальный запуск

## Предварительные условия

- Docker и Docker Compose
- Для NL-функций: ключ LLM в корневом `.env` (см. `LLM_API_KEY` в [`.example.env`](../../.example.env))

## Данные для тестов (витрина `main_db`)

Сервис **`main-db-bootstrap`** при первом `docker compose up` заливает таблицу `public.drivee_orders` из CSV через [scripts/seed_main_db.py](../../scripts/seed_main_db.py). По умолчанию в контейнере путь к файлу — `/work/dataset/train.csv`, то есть на хосте нужен файл **`dataset/train.csv` в корне репозитория** (рядом с `docker-compose.yml`):

1. Создайте каталог `dataset/`, если его ещё нет.
2. Положите туда **`train.csv`** с тестовыми строками заказов (ожидаемые колонки описаны в скрипте сида).
3. Затем выполняйте `docker compose up --build` и дождитесь успешного завершения `main-db-bootstrap`.

Без этого файла сид не сможет прочитать данные, и витрина останется пустой или шаг bootstrap завершится с ошибкой. Объём строк по умолчанию ограничен переменной **`CSV_SEED_LIMIT`** (см. [docker-compose.yml](../../docker-compose.yml)); другой путь к CSV — **`MAIN_DB_CSV_PATH`** в `.env`. Крупный `train.csv` в репозитории обычно тянется через **Git LFS** — см. [scripts/README.md](../../scripts/README.md).

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
| PostgreSQL с хоста (platform) | `localhost:5446` → контейнер `postgres-db:5432` |
| PostgreSQL с хоста (warehouse) | `localhost:5447` → контейнер `main-db:5432` |

Схемы БД, пользователи и назначение: [../infrastructure/databases.md](../infrastructure/databases.md).

## Переменные окружения

Скопируйте [`.example.env`](../../.example.env) в `.env` в том же каталоге и заполните секреты. Для фронтенда при необходимости — [`frontend/.env.example`](../../frontend/.env.example) → `frontend/.env`.

## Документация API

- BFF Swagger: `http://localhost:8000/docs` (агрегирует проксируемые контракты).
