# frontend — внутренняя архитектура

## Слойность (Feature-Sliced подход)

```mermaid
flowchart TB
    pages["pages: home, auth, reports, settings"]
    widgets["widgets: analytics-workspace, auth forms"]
    features["features: analytics, reports, ..."]
    entities["entities: auth, analytics types"]
    shared["shared: api, ui, config, lib"]
    pages --> widgets
    pages --> features
    widgets --> features
    features --> entities
    features --> shared
    entities --> shared
```

- **app/** — роутинг (`router.tsx`), layout, providers, защищённые маршруты.
- **features/analytics** — NL-чат, панель, графики, подписка на WebSocket.
- **features/reports** — задачи отчётов, модалки.
- **entities/auth** — хуки логина/регистрации.
- **shared** — axios instance, UI kit, локали.
