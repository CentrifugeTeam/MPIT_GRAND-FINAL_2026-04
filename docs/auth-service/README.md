# auth-service

## Зачем нужен

Выделенный сервис **аутентификации и учётных записей**: регистрация, вход, JWT, пользователи и роли. Хранит данные в **platform** PostgreSQL (`postgres-db`), чтобы BFF и остальная система не дублировали логику паролей и токенов.

## Границы ответственности

- Выдача и обновление access/refresh токенов.
- CRUD пользователей и ролей (см. роутеры в `app/api`).
- Не отвечает за NL-чат, аналитику и отчёты — только идентичность.

## Контракты

- **Порт (compose):** `8002`
- **HTTP:** FastAPI, базовый путь задаётся в [`app/main.py`](../../auth-service/app/main.py).
- Документация у сервиса: [`../../auth-service/README.md`](../../auth-service/README.md).

## Зависимости

- **БД:** `postgres-db` (переменные `POSTGRES_*`, `DB_HOST` в compose).

## Конфигурация

См. [`.example.env`](../../.example.env) и compose-секцию `auth-service`. Секрет `SECRET_KEY` должен совпадать с BFF для проверки JWT на шлюзе.

## Исходники

Каталог: [`../../auth-service/`](../../auth-service/).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
