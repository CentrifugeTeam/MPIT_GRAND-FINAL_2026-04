# frontend — ключевые файлы

Относительно [`frontend/`](../../frontend/).

| Путь | Роль |
|------|------|
| `vite.config.ts` | Сборка и dev-сервер. |
| `src/main.tsx` | Bootstrap React. |
| `src/app/router.tsx` | Маршрутизация. |
| `src/features/analytics/lib/subscribe-nl-chat-ws.ts` | WebSocket NL-чата. |
| `src/features/analytics/lib/use-nl-orchestrator-chat.ts` | Состояние чата. |
| `src/features/analytics/api/analytics-api.ts` | Вызовы REST аналитики через BFF. |
| `src/shared/api/axios.ts` | Базовый URL и интерцепторы. |
| `src/shared/config/env.ts` | Env для клиента. |
| `src/widgets/analytics-workspace/ui/analytics-workspace.tsx` | Сборка экрана аналитики. |

Остальные файлы в `src/features/analytics/ui/` — экранные компоненты (Figma-home, панели, графики).
