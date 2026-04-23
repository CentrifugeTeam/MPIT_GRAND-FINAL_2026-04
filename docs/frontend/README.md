# frontend

## Зачем нужен

**SPA для пользователя:** авторизация, рабочее место аналитики с NL-чатом (WebSocket), графики, отчёты, настройки. Общается с backend через **BFF** (axios + WS URL из env).

## Стек

- React, Vite, TypeScript (см. [`../../frontend/package.json`](../../frontend/package.json)).

## Контракты

- **Порт (compose):** `5173`
- Переменные: [`../../frontend/.env.example`](../../frontend/.env.example).

## Исходники

[`../../frontend/`](../../frontend/).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
