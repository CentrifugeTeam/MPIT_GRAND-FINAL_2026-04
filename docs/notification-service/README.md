# notification-service

## Зачем нужен

**Уведомления пользователя:** REST API для постановки писем в очередь **`email_queue`**, запись в platform БД. Отдельный процесс **notification-worker** в compose запускает **`email_worker.py`** и потребляет ту же очередь, отправляя письма через SMTP.

## Два runtime в Docker

| Процесс | Команда (compose) | Роль |
|---------|-------------------|------|
| `notification-service` | по умолчанию из Dockerfile | FastAPI на порту **8007**. |
| `notification-worker` | `python email_worker.py` | Consumer `email_queue` → SMTP. |

Оба используют один каталог кода [`../../notification-service/`](../../notification-service/).

## Зависимости

- `postgres-db`, RabbitMQ, SMTP (переменные `SMTP_*`).

## Исходники

Локальный [README](../../notification-service/README.md).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
