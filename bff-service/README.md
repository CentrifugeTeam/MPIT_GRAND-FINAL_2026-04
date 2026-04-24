# BFF Service (Backend For Frontend)

-------------

## Описание

API Gateway сервис, который объединяет все микросервисы и предоставляет единый API для фронтенда. Отвечает за оркестрацию запросов, аггрегацию данных и упрощение взаимодействия клиента с backend.

-------------

## Зачем выделен отдельно?

### 🎯 Основные причины:

1. **Упрощение клиента**
   - Один endpoint вместо 5-7 запросов к разным сервисам
   - Фронтенд не знает о внутренней архитектуре
   - Меньше HTTP запросов = быстрее UI

2. **Оркестрация бизнес-логики**
   - Аггрегация данных из разных сервисов
   - Обработка ошибок и retry логика

3. **Безопасность**
   - Единая точка входа для аутентификации
   - Скрывает внутренние сервисы от интернета
   - Централизованная валидация и rate limiting

4. **Гибкость**
   - Можно менять внутренние сервисы без изменения клиента
   - Версионирование API
   - A/B тестирование

-------------

## Технологии

- **Framework**: FastAPI (Python 3.11)
- **HTTP Client**: httpx (async)
- **Auth**: JWT validation
- **Async**: asyncio для параллельных запросов

-------------

## Переменные окружения

```env
# Внутренние URL сервисов
AUTH_SERVICE_URL=http://auth-service:8002
NOTIFICATION_SERVICE_URL=http://notification-service:8007
# WebSocket NL-чат: если клиент не передал источник, BFF подставит этот ключ при запросе схемы (см. analytics DEFAULT_ANALYTICS_SOURCE_KEY).
DEFAULT_ANALYTICS_SOURCE_KEY=main-db

# JWT конфиг (для валидации)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
```

-------------

## Взаимодействие с другими сервисами

- **Auth Service** → проверка JWT токенов, получение информации о пользователе
- **Files Service** → загрузка/скачивание файлов
- **Notification Service** → отправка уведомлений

## Guardrails

- Во все вызовы analytics/report-task прокидываются заголовки `X-User-Id` и `X-User-Role` (роль из JWT).
- WebSocket `chat_message` передаёт `user_role` в очередь оркестратора и при предзагрузке схемы вызывает analytics с теми же заголовками.
- **Rate limiting:** при заданном `REDIS_URL` лимит запросов к `/api/*` в минуту на пользователя (JWT `uuid`) или по IP для запросов без валидного Bearer. Переменные: `REDIS_URL`, `RATE_LIMIT_PER_MINUTE` (см. `.example.env`).
- **Аудит HTTP:** в stdout пишется одна JSON-строка на запрос (`request_audit`: `request_id`, `path`, `status_code`, `duration_ms`, `outcome`).

## Документация

Детальное описание, модули, WebSocket, очереди: [docs/bff-service/README.md](../docs/bff-service/README.md) (от корня репозитория).

