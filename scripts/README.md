# Скрипты

## Витрина `main_db` при `docker compose up`

Один сервис **`main-db-bootstrap`** вызывает [`seed_main_db.py`](seed_main_db.py): DDL `drivee_orders` + загрузка из CSV. Лимит и порог «уже достаточно строк» задаётся **`CSV_SEED_LIMIT`** (и опционально `MAIN_DB_SEED_DSN`, `MAIN_DB_CSV_PATH` в `docker-compose.yml` / `.env`).

Повторить шаг вручную:

```bash
./scripts/apply_main_db_mock.sh
```

(нужен запущенный `main-db`, например `docker compose up -d main-db`.)

## Загрузка с хоста (`seed_main_db.py`)

1. Поднимите Postgres: из корня репозитория `docker compose up -d main-db` и дождитесь health.
2. Установите зависимость (один раз): `pip install -r scripts/requirements-seed.txt`
3. Запуск (порт `5447` как в `docker-compose.yml`):

```bash
python scripts/seed_main_db.py --limit 5000
```

Полная заливка большого `train.csv` (без `--limit`) может занять заметное время.

Параметры:

- `--dsn` — URL подключения (по умолчанию `postgresql://postgres:postgres@localhost:5447/main_db`)
- `--csv` — путь к CSV (по умолчанию `sql-generator-worker/dataset/train.csv` относительно корня репо)
- `--limit N` — только первые N строк данных (после заголовка)
- `--skip-if-count-ge N` — не вставлять, если в таблице уже ≥ N строк
- `--wait-seconds S` — ждать доступность БД до S секунд
- `--replace` — `TRUNCATE` таблицы перед вставкой

Таблица: `public.drivee_orders` (создаётся при необходимости).

## Много строк из CSV в Docker (без Python на хосте)

Тот же bootstrap, лимит с хоста:

```bash
CSV_SEED_LIMIT=50000 docker compose run --rm main-db-bootstrap
```

Compose подставляет env в сервис (см. `docker-compose.yml`).
