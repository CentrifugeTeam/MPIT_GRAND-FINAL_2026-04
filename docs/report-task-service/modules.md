# report-task-service — модули

| Путь | Назначение |
|------|------------|
| `app/main.py` | FastAPI, подключение роутера задач. |
| `app/core/config.py` | DSN платформы, RabbitMQ, интервал диспетчера, internal token. |
| `app/core/queues.py` | Имя очереди отчётов. |
| `app/api/tasks.py` | CRUD задач, ручной enqueue прогона. |
| `app/schemas/tasks.py` | Pydantic-схемы. |
| `app/db/models.py` | ORM задач и прогонов. |
| `app/db/session.py` | Сессии SQLAlchemy. |
| `app/db/base.py` | Declarative base. |
| `app/services/task_store.py` | Бизнес-логика задач. |
| `app/services/run_store.py` | Прогоны отчётов. |
| `app/services/schedule.py` | Расписания (cron-подобная логика). |
| `app/services/scheduler.py` | Цикл диспетчера и публикация в MQ. |
| `app/services/rabbitmq_publish.py` | Async publish в очередь. |
