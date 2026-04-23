# auth-service — ключевые файлы

Пути относительно корня [`auth-service/`](../../auth-service/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Сборка образа (development target в compose). |
| `app/main.py` | Приложение FastAPI. |
| `app/core/config.py` | `Settings` из env. |
| `app/api/auth.py` | Эндпоинты аутентификации. |
| `app/api/users.py` | Пользователи. |
| `app/api/roles.py` | Роли. |
| `app/models.py` | Таблицы БД. |
| `app/database.py` | Подключение к PostgreSQL. |
| `app/crud.py` | Бизнес-операции над пользователями. |
| `app/role_crud.py` | Операции над ролями. |
| `app/schemas.py` | Валидация API. |
| `app/utils/auth.py` | JWT и безопасность паролей. |
| `app/db_migrate.py` | Миграции при запуске. |
