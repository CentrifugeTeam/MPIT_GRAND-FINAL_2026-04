# Базы данных

## postgres-db (platform)

- **Контейнер:** `postgres-db`
- **Порт с хоста:** `5446` → `5432` в контейнере
- **Назначение:** метаданные платформы (пользователи auth-service, уведомления notification-service, задачи отчётов и т.д. — по фактическим моделям сервисов).
- **Пользователь по умолчанию:** `postgres` / БД `postgres-db` (см. compose).

## main-db (warehouse / аналитика)

- **Контейнер:** `main-db`
- **Порт с хоста:** `5447` → `5432`
- **Назначение:** витрина данных для аналитики и NL→SQL (`ANALYTICS_DATABASE_URL` указывает сюда).
- **Схема и данные:** сервис `main-db-bootstrap` после healthy `main-db` запускает [`scripts/seed_main_db.py`](../../scripts/seed_main_db.py) с CSV (путь `MAIN_DB_CSV_PATH`, лимит `CSV_SEED_LIMIT`).

## Связь с сервисами

| Сервис | БД |
|--------|-----|
| auth-service | postgres-db |
| notification-service | postgres-db |
| report-task-service | postgres-db |
| analytics-service | main-db (аналитика) + postgres-db (платформа, чаты, политики) |

Подробнее про использование в коде: [../analytics-service/architecture.md](../analytics-service/architecture.md), [../auth-service/architecture.md](../auth-service/architecture.md).
