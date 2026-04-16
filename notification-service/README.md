# Notification Service

-------------

## Описание

Сервис управления уведомлениями. Отвечает за отправку email уведомлений, push уведомлений и управление историей уведомлений через RabbitMQ очередь.

-------------

## Зачем выделен отдельно?

### 🎯 Основные причины:

1. **Асинхронная обработка**
   - Отправка email не блокирует основные операции
   - Очередь RabbitMQ для надёжной доставки
   - Retry механизм при сбоях SMTP

2. **Независимость от внешних сервисов**
   - Изоляция работы с SMTP серверами
   - Сбой почты не ломает всю систему
   - Можно легко переключиться на другой email провайдер

3. **Масштабируемость**
   - Независимое масштабирование workers
   - Пиковые нагрузки (массовая рассылка) не влияют на другие сервисы
   - Легко добавить приоритеты уведомлений

4. **Переиспользование**
   - Единый механизм уведомлений для всей системы
   - Легко добавить новые каналы (SMS, Telegram, Slack)
   - Централизованная история всех уведомлений

-------------

## Технологии

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (история уведомлений)
- **Message Queue**: RabbitMQ (pika)
- **Email**: SMTP (Gmail, Yandex, custom)
- **ORM**: SQLAlchemy
- **Workers**: Celery-like background workers

-------------

## Переменные окружения

```env
DATABASE_URL=postgresql://postgres:postgres@postgres-db:5432/postgres-db

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# SMTP (Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourapp.com
```

-------------

## Взаимодействие с другими сервисами

- **BFF Service** → получение запросов на отправку уведомлений
- **Auth Service** → получение email адресов пользователей
- **RabbitMQ** → получение задач из очереди для асинхронной обработки

