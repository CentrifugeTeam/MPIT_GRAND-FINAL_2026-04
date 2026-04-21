# База `main_db` (аналитическая витрина)

## Миграции

Отдельного **Alembic / Flyway для `main_db`** в репозитории нет: таблица `public.drivee_orders` создаётся в **`scripts/seed_main_db.py`** (DDL в константе `DDL`) и заполняется из CSV тем же скриптом.

Таблицы **platform** (`nl_sql_jobs`, `analytics_data_sources`, …) в `postgres-db` создаются **analytics-service** при старте через SQLAlchemy `create_all` (см. `analytics-service/app/db/platform_session.py`), это не классические миграции.

## Заполнение при `docker compose up`

Сервис **`main-db-bootstrap`** (см. `docker-compose.yml`) после health `main-db` запускает `seed_main_db.py`: создаёт таблицу при необходимости и вставляет до `CSV_SEED_LIMIT` строк из CSV (если в таблице уже не меньше этого числа строк — пропуск). Параметры задаются env: `MAIN_DB_SEED_DSN`, `MAIN_DB_CSV_PATH`, `CSV_SEED_LIMIT`.

`analytics-service` и `sql-generator-worker` ждут успешного завершения `main-db-bootstrap`.

Требуется **Docker Compose v2.20+** (условие `service_completed_successfully`).

## Ручной повтор

Из корня репозитория (нужен запущенный `main-db`):

```bash
./scripts/apply_main_db_mock.sh
```

Или полный CSV с хоста: `python scripts/seed_main_db.py` (см. `scripts/README.md`).
