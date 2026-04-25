# frontend — ключевые файлы

Относительно [`frontend/`](../../frontend/). Подробности по WebSocket — [websocket-client.md](websocket-client.md) и [nl-chat-and-reports.md](nl-chat-and-reports.md).

| Путь | Роль |
|------|------|
| `vite.config.ts` | Сборка и dev-сервер. |
| `src/main.tsx` | Bootstrap React. |
| `src/app/router.tsx` | Маршрутизация. |
| `src/features/analytics/lib/subscribe-nl-chat-ws.ts` | WebSocket NL-чата, в т.ч. `chat_messages_deleted`. |
| `src/features/analytics/lib/use-nl-orchestrator-chat.ts` | Состояние чата, merge ассистента, retry/удаление. |
| `src/features/analytics/lib/nl-chat-transcript.ts` | Загрузка/нормализация транскрипта. |
| `src/features/analytics/ui/analytics-panel/nl-chat-transcript-block.tsx` | Лента сообщений, тулбар (`assistantActionsLocked` / `composerBusy`). |
| `src/features/analytics/ui/figma-home/figma-analytics-main.tsx` | Состав экрана аналитики и чата; шаринг / клон для viewer. |
| `src/features/analytics/ui/figma-home/figma-share-chat-emails-modal.tsx` | Модалка приглашений по email. |
| `src/features/analytics/ui/figma-home/figma-share-access-modal.tsx` | Модалка «поделиться чатом» (доступ). |
| `src/features/analytics/ui/figma-home/figma-pending-invites-strip.tsx` | Полоска ожидающих инвайтов. |
| `src/features/analytics/ui/figma-home/figma-sidebar-notifications-button.tsx` | Кнопка уведомлений в сайдбаре. |
| `src/features/analytics/model/use-pending-chat-invites.ts` / `use-accepted-chat-invites.ts` | Загрузка инвайтов для UI. |
| `src/features/reports/ui/create-report-modal.tsx` | Создание/редактирование отчёта, фокус в модалку при открытии. |
| Сквозной разбор | [nl-chat-and-reports.md](nl-chat-and-reports.md) (WS, REST, воркер, UX). |
| `src/features/analytics/api/analytics-api.ts` | Вызовы REST аналитики через BFF; `fetchNlChatPdfBlob` и разбор `Content-Disposition` для PDF. |
| `src/features/analytics/model/use-chat-suggestions.ts` | Загрузка серверных FAQ-подсказок (chat suggestions) для чата. |
| `src/shared/api/axios.ts` | Базовый URL и интерцепторы. |
| `src/shared/config/env.ts` | Env для клиента. |
| `src/widgets/analytics-workspace/ui/analytics-workspace.tsx` | Сборка экрана аналитики. |

Остальные файлы в `src/features/analytics/ui/` — экранные компоненты (Figma-home, панели, графики).
