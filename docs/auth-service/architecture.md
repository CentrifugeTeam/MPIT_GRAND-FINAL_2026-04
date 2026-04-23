# auth-service — внутренняя архитектура

## Слои

```mermaid
flowchart TB
    subgraph api [HTTP API]
        routes["app/api: auth, users, roles"]
    end
    subgraph domain [Домен]
        crud["crud.py / role_crud.py"]
        utils["utils/auth.py JWT и пароли"]
    end
    subgraph data [Данные]
        models["SQLAlchemy models"]
        db["database.py сессии"]
    end
    routes --> crud
    routes --> utils
    crud --> models
    crud --> db
```

## Типовой сценарий

1. Клиент обращается к **BFF** `/api/auth/*`.
2. BFF проксирует запрос в **auth-service**.
3. Сервис проверяет учётные данные, читает/пишет строки в `postgres-db`, возвращает токены или профиль.

## Миграции

[`app/db_migrate.py`](../../auth-service/app/db_migrate.py) — инициализация/обновление схемы при старте (см. `main.py`).
