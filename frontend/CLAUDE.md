# Проект: hackathon-2026-1

React 19 веб-приложение на Vite.

## Стек

- **Сборка**: Vite 8, TypeScript 5.9
- **UI-фреймворк**: React 19, React DOM
- **Навигация**: React Router v7 (file-based или декларативный)
- **UI**: HeroUI React v3 (compound components), Tailwind CSS v4
- **Data fetching**: TanStack Query v5 + Axios + Zod v4
- **Формы**: React Hook Form + @hookform/resolvers (Zod)
- **State**: Zustand (глобальный), React Query (серверный), useState (локальный)
- **Хранилище**: localStorage (токены — через Zustand persist)
- **Пакетный менеджер**: bun

## Стилизация

- Использовать **Tailwind CSS v4** (utility-first классы через `className`) — основной способ стилизации.
- Компоненты **HeroUI React v3** использовать как основу для UI — compound components (например `Card.Header`, `Card.Content`).
- Inline `style={{}}` — только когда Tailwind не покрывает (анимации, динамические значения).
- Тема и токены: использовать переменные HeroUI (`--color-accent`, `--radius-md` и т.д.), не хардкодить цвета.
- HeroUI v3 **не требует Provider** — стили подключаются через `@import "@heroui/styles"` в CSS.

## Тема (Light / Dark)

- HeroUI React v3 предоставляет light/dark переменные из коробки через `@heroui/styles`.
- Переключение темы: управлять классом `dark` на `<html>` или через CSS `prefers-color-scheme`.
- **Семантические классы**: использовать `bg-background`, `text-foreground`, `bg-surface`, `text-muted` и т.д. — они автоматически адаптируются к теме.
- **Не хардкодить** цвета (`#ffffff`, `#000000`) в компонентах — только семантические токены.
- Кастомизация цветов — через `index.css` в `@theme { ... }` или `@layer theme { ... }`.

### Переменные темы (основные)

| Переменная | Назначение |
|---|---|
| `background` / `foreground` | Основной фон и текст |
| `surface` / `surface-foreground` | Карточки, аккордеоны |
| `overlay` / `overlay-foreground` | Модалки, поповеры |
| `accent` / `accent-foreground` | Акцентный цвет (кнопки, ссылки) |
| `default` / `default-foreground` | Нейтральные элементы |
| `success` / `warning` / `danger` | Статусные цвета |
| `muted` | Приглушённый текст |
| `separator` / `border` | Разделители и границы |

## Архитектура (FSD, адаптированная под React Router)

```
src/
  app/                    # Инициализация приложения, providers, router
    router.tsx            # React Router конфигурация
    providers.tsx         # QueryClient, Theme, etc.
    layout.tsx            # Root layout
  pages/                  # Страницы (маршруты), собирают виджеты
    home/
    auth/
    ...
  widgets/                # Композитные блоки UI (собирают features + entities)
  features/               # Бизнес-фичи (user actions, формы, кнопки с логикой)
  entities/               # Бизнес-сущности (user, product и т.д.)
    <entity>/
      model/              # Типы, схемы Zod, хуки запросов
      ui/                 # Компоненты отображения сущности
      api/                # API-функции для сущности
  shared/                 # Переиспользуемое без бизнес-логики
    ui/                   # Базовые UI-компоненты
    lib/                  # Утилиты, хелперы
    api/                  # Axios instance, interceptors
    config/               # Константы, env
```

### Правила слоёв

- **app/** — инициализация, providers, роутер. Никакой бизнес-логики.
- **pages/** — страницы-маршруты. Собирают виджеты в экраны. Минимум логики.
- **widgets/** — собирают features и entities в готовые блоки для страниц.
- **features/** — одна фича = одна пользовательская задача. Может импортировать entities и shared.
- **entities/** — доменные модели. Может импортировать только shared.
- **shared/** — никаких зависимостей на верхние слои.
- **Импорт строго сверху вниз**: app → pages → widgets → features → entities → shared.

## Типизация API-ответов

- **Каждый** ответ API обязательно типизировать через **Zod-схему**.
- Схема определяется в `entities/<entity>/model/schema.ts`.
- Из схемы выводить TypeScript-тип: `type Entity = z.infer<typeof entitySchema>`.
- В API-функции вызывать `.parse(data)` — это и валидация, и типизация в одном шаге.
- Никогда не использовать `as` или ручные интерфейсы для API-данных — только Zod.

## API и Data Fetching

- Все API-вызовы через **Axios instance** из `shared/api/axios.ts`.
- Ответы API **валидировать через Zod-схемы** на уровне entities (см. секцию выше).
- Хуки запросов создавать через **TanStack Query**:
  - `useQuery` для GET-запросов
  - `useMutation` для POST/PUT/DELETE
- Query keys — массивы: `['entity', id]`, `['entity', 'list', filters]`.
- Хуки запросов размещать в `entities/<entity>/model/` или `features/<feature>/api/`.

## State Management

- **Серверные данные** → TanStack Query (кэш, рефетч, оптимистичные обновления). Не дублировать в Zustand.
- **Глобальный UI-стейт** (тема, auth-статус, модалки) → Zustand (`shared/lib/` или отдельные сторы).
- **Локальный стейт** (формы, toggle, временные значения) → `useState` / React Hook Form.
- Правило: если данные приходят с сервера — это React Query. Если это клиентский стейт — Zustand или useState.

## Path Aliases

- `@/*` → `src/*` (настроить в tsconfig.json и vite.config.ts).
- Импорты: `import { api } from "@/shared/api/axios"`, `import { UserCard } from "@/entities/user/ui"`.

## Команды

- `bun dev` — запуск dev-сервера (Vite)
- `bun run build` — сборка для продакшена
- `bun run lint` — линтинг (ESLint)
- `bunx tsc --noEmit` — проверка типов
