# frontend — модули

| Путь | Назначение |
|------|------------|
| `src/app/router.tsx` | Маршруты приложения. |
| `src/app/layout.tsx` | Корневой layout. |
| `src/app/providers.tsx` | React Query / тема / провайдеры. |
| `src/app/protected-route.tsx` | Защита маршрутов по сессии. |
| `src/app/guest-route.tsx` | Маршруты только для гостя. |
| `src/pages/*` | Страницы по URL. |
| `src/widgets/*` | Крупные блоки UI (воркспейс, формы). |
| `src/features/analytics/*` | NL-чат, графики, боковая панель, Figma-стилизованный UI. |
| `src/features/reports/*` | Дашборд отчётов, детали задачи. |
| `src/features/analytics-chat` и др. | Точечные фичи (реэкспорты). |
| `src/entities/auth/*` | Типы и хуки аутентификации. |
| `src/entities/analytics/*` | Модели схемы и т.д. |
| `src/shared/api/axios.ts` | HTTP-клиент к BFF. |
| `src/shared/config/env.ts` | Публичные env (`VITE_*`). |
| `src/shared/lib/auth-store.ts` | Состояние сессии. |
| `src/shared/ui/*` | Атомы, молекулы, организмы. |
