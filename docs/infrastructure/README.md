# Инфраструктура

Компоненты, которые не являются отдельными папками приложения в `docker-compose.yml`, но определяют среду выполнения.

| Документ | Тема |
|----------|------|
| [databases.md](databases.md) | PostgreSQL (`postgres-db`, `main-db`), bootstrap, CSV seed |
| [messaging.md](messaging.md) | RabbitMQ: очереди и кто публикует/потребляет |
| [edge.md](edge.md) | Nginx, Redis, CloudPub |

Конфигурация compose: [`../../docker-compose.yml`](../../docker-compose.yml). Переменные окружения: [`.example.env`](../../.example.env).
