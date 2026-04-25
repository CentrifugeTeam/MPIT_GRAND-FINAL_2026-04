# notification-service

## Зачем нужен

**Уведомления пользователя:** REST API для постановки записей в platform БД и (для подходящих типов) писем в очередь **`email_queue`**. Отдельный процесс **notification-worker** в compose запускает **`email_worker.py`** и потребляет очередь, отправляя письма через SMTP.

**Тип `chat_invite`:** enum `NotificationType.CHAT_INVITE` / строка `"chat_invite"` в API. BFF при `POST /api/analytics/chats/{id}/share-invites` для каждого приглашённого пользователя вызывает `POST .../notifications/{user_id}/notify` с `type=chat_invite` и `payload` (`invite_id`, `conversation_id`, владелец, заголовок чата): создаётся запись in-app в БД и, по общему пути, публикация в `email_queue`. **notification-worker** при обработке `chat_invite` **не отправляет SMTP** (ранний выход в [`rabbitmq_service.process_notification`](../../notification-service/app/services/rabbitmq_service.py)). В `main.py` при старте выполняется миграция enum в PostgreSQL, если значение `chat_invite` ещё не добавлено.

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
