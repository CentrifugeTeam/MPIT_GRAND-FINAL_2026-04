# Глоссарий

Термины, которые встречаются в коде и документации. Полный перечень реализованных модулей и путей в коде: [implementation-scope.md](implementation-scope.md). Кейс Drivee (ТЗ): [requirements/case-drivee.md](requirements/case-drivee.md); экспертное сопоставление с ТЗ: [requirements/EXPERT_REVIEW_DRIVEE.md](requirements/EXPERT_REVIEW_DRIVEE.md).

## Продукт и домен

| Термин | Описание |
|--------|----------|
| **Drivee / кейс** | Бизнес-сценарий соревнования; детали — в `requirements/case-drivee.md`, когда текст ТЗ будет перенесён в репозиторий. |
| **Заказы (warehouse)** | Аналитические данные в `main_db`, таблица `public.drivee_orders` (сид из `dataset/train.csv`; см. [operations/local-run.md](operations/local-run.md), [infrastructure/databases.md](infrastructure/databases.md)). |
| **NL→SQL** | Конвейер: вопрос на естественном языке → LLM и схема БД → SQL → валидация (guardrails) → выполнение на warehouse → таблица и рекомендуемый график в ответе чата. |
| **Семантический слой (глоссарий метрик)** | JSON-справочник бизнес-терминов с синонимами и подсказками для SQL; подмешивается в промпт при генерации. Файл [metrics_glossary.json](../analytics-service/app/data/metrics_glossary.json), логика — `metrics_glossary.py`. |
| **Разбор вопроса (interpret)** | API `POST /interpret-question`: эвристический confidence, предупреждения и совпадения с глоссарием **без** выполнения SQL. |
| **Оценка качества запроса (query-quality)** | API `POST /query-quality`: LLM оценивает согласованность вопроса и SQL без исполнения. |
| **Отчётная задача (report task)** | Сохранённый сценарий с текстом инструкции NL, привязкой к источнику данных и **расписанием** (once / daily / weekly / …); диспетчер ставит прогоны в очередь. Сервис [report-task-service](../report-task-service/). |
| **Шаблон отчёта (task template)** | Переиспользуемый пресет для отчётных задач; API и UI карусели шаблонов. |
| **Прогон отчёта (report run)** | Одно выполнение задачи: сообщение в `report_task_incoming_v1` → тот же NL-контур, что и интерактивный чат (`conversation_id` вида `__report_run__`). |

## Архитектура

| Термин | Описание |
|--------|----------|
| **BFF** | Backend-for-frontend: единая HTTP/WebSocket/SSE точка для клиента, прокси к микросервисам; consumer результатов SQL из RabbitMQ. |
| **auth-service** | Регистрация, логин, refresh JWT, пользователи, справочник ролей. |
| **analytics-service** | Схема БД, interpret, чаты, история, источники данных, политики доступа (ADMIN), внутренний sync чата для оркестратора, фоновые consumer’ы (подсказки чата, шаблоны отчётов), плановое обновление кэша схемы. |
| **sql-generator-worker** | Читает `nl_sql_generate_request`, вызывает LLM, **guardrails** (`sql_guard`), выполняет SQL, публикует результат в `nl_sql_generate_result` и `nl_sql_generate_result_chat`. |
| **nl-orchestrator-worker** | Ведёт диалог LLM, стриминг «рассуждений», при низком confidence — уточняющий ответ без SQL; ставит задачи воркеру SQL; синхронизирует историю в analytics. |
| **report-task-service** | CRUD задач и шаблонов, расписание (APScheduler), постановка прогонов в очередь. |
| **notification-service** | REST уведомлений; постановка писем в `email_queue`; worker’ы отправки. |
| **Platform DB** | PostgreSQL `postgres-db`: пользователи, чаты, nl_sql_jobs, источники, политики, уведомления. |
| **Main DB / warehouse** | PostgreSQL `main-db`: витрина для аналитики и NL→SQL по кейсу. |
| **Источник данных (analytics source)** | Именованный DSN к БД; хранение и выбор ключа на платформе; в compose — `ANALYTICS_SOURCES_INLINE` и связанные переменные. |
| **Политика доступа (access policy)** | Для пары роль + источник: разрешённые таблицы, запрещённые колонки и т.д.; влияет на выдачу схемы и на **sql_guard** при выполнении. |
| **NL-чат** | Диалог на естественном языке с генерацией SQL и ответов: BFF (`chat_mq`) ↔ очереди `nl_chat_incoming` / `nl_chat_out` ↔ nl-orchestrator-worker; с фронта — WebSocket. Подробно: [frontend/nl-chat-and-reports.md](frontend/nl-chat-and-reports.md). |
| **Ссылка на чат (deep link)** | Маршрут фронта **`/home/{conversationId}`** — открытие той же NL-сессии; совместный просмотр после инвайта; при доступе viewer — опция **клонировать** к себе. |
| **Инвайт на чат (chat invite)** | Приглашение по email к совместному просмотру сессии NL-чата; platform DB, BFF: `share-invites`, `chat-invites`, `answer`. |
| **Клон расшаренного чата** | `POST .../chats/{conversation_id}/clone-for-me` (BFF → analytics): копия чата в списке «своих» у приглашённого. |
| **Экспорт ответа в PDF** | BFF тянет транскрипт из analytics, собирает PDF (ReportLab); query `message_id` — UUID сообщения assistant. |

## Очереди RabbitMQ

Имена и участники — в [infrastructure/messaging.md](infrastructure/messaging.md). Кратко:

| Термин | Описание |
|--------|----------|
| **`nl_sql_generate_request` / `nl_sql_generate_result`** | Асинхронная генерация и выполнение SQL; результат забирает BFF для UI и (ветка чата) оркестратор через **`nl_sql_generate_result_chat`**. |
| **`nl_chat_incoming` / `nl_chat_out`** | Очередь сообщений пользователя к оркестратору и обратно к BFF для рассылки в WebSocket-комнату. |
| **`report_task_incoming_v1`** | Запуск сохранённого отчёта по расписанию в NL-оркестраторе. |
| **`report_template_plan_request_v1`** | Инициализация/дедуп шаблонов отчётов после изменения источников. |
| **`email_queue`** | Асинхронная отправка email worker’ом. |

## Безопасность и качество данных

| Термин | Описание |
|--------|----------|
| **Guardrails SQL** | Парсинг AST (sqlglot): только `SELECT`, один statement, запрет DDL/DML и опасных функций, проверка таблиц/колонок по схеме и политике, лимит строк, whitelist таблиц. Реализация: `sql_guard.py` в sql-generator-worker. |
| **`X-User-Id` / `X-User-Role`** | Заголовки, которые BFF проставляет при прокси на основе JWT; роль **ADMIN** обходит часть ограничений схемы и даёт CRUD политик доступа. |

## Технические

| Термин | Описание |
|--------|----------|
| **JWT** | Access-токен после логина; refresh по контракту auth-service; BFF валидирует и прокидывает `X-User-Id`, `X-User-Role`. |
| **Internal token** | Секреты вроде `INTERNAL_NL_CHAT_SYNC_TOKEN`, `REPORT_TASK_INTERNAL_TOKEN` для вызовов между сервисами (оркестратор → analytics и т.д.). |
| **WebSocket (NL-чат)** | Соединение UI ↔ BFF `/api/websocket/ws`; отдельная выдача краткоживущего токена для подключения. См. [frontend/websocket-client.md](frontend/websocket-client.md). |
| **SSE (Server-Sent Events)** | Поток уведомлений в браузер: `GET /api/notification/stream?token=...`, `Content-Type: text/event-stream`; при наличии Redis — pub/sub на обновления, иначе редкий poll. Клиент: `EventSource`, хуки `use-notifications-sse`. |
| **Redis** | Опционально: rate limit на BFF; канал real-time для SSE-уведомлений (`notification_realtime`). |
| **Rate limit / audit** | Middleware на BFF и analytics-service: ограничение частоты запросов и журналирование обращений. |
