# Реализованные возможности

Ниже — что есть в коде и compose сегодня (куда смотреть в репозитории и в доке по сервисам). Перечень **расширен** относительно ранней версии: включены семантика, guardrails, фоновые consumer’ы analytics-service, страницы фронта, админские политики и т.д.

| Возможность | Где в проекте |
|-------------|----------------|
| Микросервисная архитектура, BFF для фронта | [bff-service](../bff-service/), [docs/bff-service/](bff-service/README.md) |
| Аутентификация и роли | [auth-service](../auth-service/) (`/auth`, `/users`, `/roles`), JWT и refresh, прокси BFF [`auth.py`](../bff-service/app/api/auth.py) |
| Две БД: платформа и витрина аналитики | [infrastructure/databases.md](infrastructure/databases.md), `docker-compose.yml` |
| Загрузка / сид витрины из CSV (`drivee_orders`), bootstrap в compose | `main-db-bootstrap`, [scripts/seed_main_db.py](../scripts/seed_main_db.py), [scripts/README.md](../scripts/README.md); датасет `dataset/train.csv` (Git LFS, см. scripts README) |
| NL→SQL: схема БД, кэш схемы, история задач и чатов | [analytics-service](../analytics-service/), [docs/analytics-service/](analytics-service/README.md); кэш и cron обновления — [`schema_cache`](../analytics-service/app/services/schema_cache.py), [`schema_scheduler`](../analytics-service/app/services/schema_scheduler.py) |
| Семантический слой: глоссарий метрик (синонимы, подсказки SQL для LLM) | [metrics_glossary.py](../analytics-service/app/services/metrics_glossary.py), [metrics_glossary.json](../analytics-service/app/data/metrics_glossary.json) |
| Разбор вопроса без SQL: confidence, предупреждения, совпадения глоссария | `POST /interpret-question` — [analytics.py](../analytics-service/app/api/analytics.py); эвристика — [question_interpretation.py](../analytics-service/app/services/question_interpretation.py) |
| LLM-оценка качества вопроса/SQL (без выполнения) | `POST /query-quality` — [analytics.py](../analytics-service/app/api/analytics.py); [query_quality_llm.py](../analytics-service/app/services/query_quality_llm.py) |
| Маскирование чувствительных фрагментов в тексте вопроса | [sensitive_redaction.py](../analytics-service/app/services/sensitive_redaction.py) |
| Серверные подсказки / FAQ для чата по источнику и локали | `GET /chat-suggestions` — [analytics.py](../analytics-service/app/api/analytics.py); [chat_suggestions_store.py](../analytics-service/app/services/chat_suggestions_store.py); фоновая догрузка — [chat_suggestion_queue_consumer.py](../analytics-service/app/services/chat_suggestion_queue_consumer.py) |
| CRUD источников данных (DSN на платформе) | [data_sources.py](../analytics-service/app/api/data_sources.py) |
| ADMIN: CRUD политик доступа к источникам по роли | [access_policies.py](../analytics-service/app/api/access_policies.py), [access_policy_store.py](../analytics-service/app/services/access_policy_store.py) |
| Асинхронная генерация и выполнение SQL воркером | [sql-generator-worker](../sql-generator-worker/) — очередь `nl_sql_generate_request`; LLM и исполнение — [worker_main.py](../sql-generator-worker/app/worker_main.py), [llm_service.py](../sql-generator-worker/app/services/llm_service.py), [query_executor.py](../sql-generator-worker/app/services/query_executor.py) |
| Guardrails SQL до выполнения (SELECT-only, схема, whitelist, политика колонок, LIMIT) | [sql_guard.py](../sql-generator-worker/app/services/sql_guard.py) |
| Автовыбор типа графика по результату (line / bar / table) | [chart_builder.py](../sql-generator-worker/app/services/chart_builder.py) |
| Учёт задач NL-SQL на платформе | [job_store.py](../analytics-service/app/services/job_store.py), [job_db.py](../sql-generator-worker/app/services/job_db.py) |
| NL-чат с оркестрацией и LLM (план, стриминг reasoning, уточнения при низком confidence) | [nl-orchestrator-worker](../nl-orchestrator-worker/), [worker_main.py](../nl-orchestrator-worker/app/worker_main.py), [chat_llm.py](../nl-orchestrator-worker/app/services/chat_llm.py); очереди `nl_chat_*` |
| Внутренний sync истории чата (оркестратор → analytics) | `POST .../internal/nl-chat-sync` в [analytics.py](../analytics-service/app/api/analytics.py) (токен `X-Chat-Sync-Token`) |
| Consumer шаблонов отчётов в analytics (очередь от report-task / инициализация) | [report_template_queue_consumer.py](../analytics-service/app/services/report_template_queue_consumer.py), lifespan в [main.py](../analytics-service/app/main.py) |
| WebSocket от UI через BFF; служебные HTTP для WS | [websocket.py](../bff-service/app/api/websocket.py) (`/token`, `/info`, `/ws`); клиент — [docs/frontend/websocket-client.md](frontend/websocket-client.md) |
| Публикация входящих сообщений чата в RabbitMQ и доставка исходящих | [chat_mq.py](../bff-service/app/services/chat_mq.py) |
| BFF: consumer результатов `nl_sql_generate_result` для сессий | [analytics_mq_consumer.py](../bff-service/app/services/analytics_mq_consumer.py), lifespan [main.py](../bff-service/app/main.py) |
| NL-чат: удаление хвоста/сообщений по WS, синхрон с БД | [docs/frontend/nl-chat-and-reports.md](frontend/nl-chat-and-reports.md), [chat_store.py](../analytics-service/app/services/chat_store.py) |
| Экспорт одного ответа ассистента в PDF (через BFF) | [nl_chat_pdf.py](../bff-service/app/services/nl_chat_pdf.py), [analytics.py `export_nl_chat_pdf`](../bff-service/app/api/analytics.py), [analytics-api.ts](../frontend/src/features/analytics/api/analytics-api.ts); см. [nl-chat-and-reports.md](frontend/nl-chat-and-reports.md) |
| Совместные чаты: инвайты по email, accept/reject, клон, мета и роль доступа | BFF: [analytics.py](../bff-service/app/api/analytics.py); analytics: [analytics.py](../analytics-service/app/api/analytics.py), [chat_store.py](../analytics-service/app/services/chat_store.py); UI: [figma-share-*](../frontend/src/features/analytics/ui/figma-home/), [nl-chat-and-reports.md](frontend/nl-chat-and-reports.md) |
| Модалка «Отчёт» из чата, дашборд отчётов, шаблоны каруселью, детали задачи | [create-report-modal.tsx](../frontend/src/features/reports/ui/create-report-modal.tsx), [reports-dashboard.tsx](../frontend/src/features/reports/ui/reports-dashboard.tsx), [report-templates-carousel.tsx](../frontend/src/features/reports/ui/report-templates-carousel.tsx), [task-detail-panel.tsx](../frontend/src/features/reports/ui/task-detail-panel.tsx) |
| Домашний экран аналитики (Figma-оболочка): сайдбар, источник, история, композер, графики | [figma-analytics-main.tsx](../frontend/src/features/analytics/ui/figma-home/figma-analytics-main.tsx), [analytics-panel](../frontend/src/features/analytics/ui/analytics-panel/), [interpretation-banner.tsx](../frontend/src/features/analytics/ui/analytics-panel/interpretation-banner.tsx) |
| Визуализации в UI: auto, bar, line, area, pie | [analytics-charts.tsx](../frontend/src/features/analytics/ui/analytics-charts/analytics-charts.tsx), [build-chart-option.ts](../frontend/src/features/analytics/ui/analytics-charts/lib/build-chart-option.ts) |
| Локализация UI (ru / en) | [frontend/src/shared/config/locales/](../frontend/src/shared/config/locales/) |
| Страницы: логин/регистрация, home, отчёты | [pages/auth/login](../frontend/src/pages/auth/login/index.tsx), [register](../frontend/src/pages/auth/register/index.tsx), [home](../frontend/src/pages/home/index.tsx), [reports](../frontend/src/pages/reports/index.tsx) |
| Источники данных и политики доступа (чтение для пользователя) | [data_sources.py](../analytics-service/app/api/data_sources.py), `access_policies` в БД платформы |
| Отчётные задачи, расписание (daily/weekly/…/once), прогоны | [report-task-service](../report-task-service/), очередь `report_task_incoming_v1`; BFF — [report_tasks.py](../bff-service/app/api/report_tasks.py) (`/api/report-tasks`) |
| Шаблоны отчётных задач (API + UI) | [report-task-service/app/api/templates.py](../report-task-service/app/api/templates.py), [use-report-templates.ts](../frontend/src/features/reports/model/use-report-templates.ts) |
| Уведомления (API), email через очередь и worker | [notification-service](../notification-service/) ([notifications.py](../notification-service/app/api/notifications.py), [email_worker.py](../notification-service/email_worker.py), [worker.py](../notification-service/worker.py)) |
| Уведомления и настройки через BFF | [notification.py](../bff-service/app/api/notification.py) (`/api/notification`) |
| Rate limit и аудит на шлюзе (BFF + analytics) | [bff-service/app/middleware/](../bff-service/app/middleware/), [analytics-service/app/middleware/](../analytics-service/app/middleware/) |
| Nginx и опциональный CloudPub, Redis | [infrastructure/edge.md](infrastructure/edge.md) |
| Очереди и участники | [infrastructure/messaging.md](infrastructure/messaging.md) |
| Сопоставление с формулировками кейса Drivee (экспертно) | [requirements/EXPERT_REVIEW_DRIVEE.md](requirements/EXPERT_REVIEW_DRIVEE.md) |

При добавлении новых публичных сценариев обновляйте этот файл и при необходимости [architecture.md](architecture.md).
