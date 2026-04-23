# auth-service — модули

| Пакет / модуль | Назначение |
|----------------|------------|
| `app/main.py` | Точка входа FastAPI, подключение роутеров, lifespan. |
| `app/core/config.py` | Настройки из окружения (DSN, JWT, секреты). |
| `app/api/auth.py` | Регистрация, логин, refresh, текущий пользователь. |
| `app/api/users.py` | Операции с пользователями (админ/сервисные сценарии). |
| `app/api/roles.py` | Роли. |
| `app/schemas.py` | Pydantic-схемы запросов/ответов. |
| `app/models.py` | ORM-модели PostgreSQL. |
| `app/database.py` | Engine и фабрика сессий. |
| `app/crud.py` | Репозиторий пользователей. |
| `app/role_crud.py` | Репозиторий ролей. |
| `app/utils/auth.py` | Хеширование паролей, создание/декодирование JWT. |
| `app/db_migrate.py` | DDL/миграции на старте. |
