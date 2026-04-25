# frontend

## Зачем нужен

**SPA для пользователя:** авторизация, рабочее место аналитики с NL-чатом (WebSocket), графики, отчёты, настройки, in-app уведомления (**SSE** к BFF). Общается с backend через **BFF** (axios + WS + EventSource, URL из env).

## Стек

- React, Vite, TypeScript (см. [`../../frontend/package.json`](../../frontend/package.json)).

## Контракты

- **Порт (compose):** `5173`
- Переменные: [`../../frontend/.env.example`](../../frontend/.env.example).
- Клиентский WebSocket (подключение, статусы, хуки): [websocket-client.md](websocket-client.md).
- NL-чат, удаление ленты, отчёты, WS BFF (плоский JSON): [nl-chat-and-reports.md](nl-chat-and-reports.md).

## Исходники

Код: [`../../frontend/`](../../frontend/) · в корне приложения — краткий [`README.md`](../../frontend/README.md) со ссылкой сюда.

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
