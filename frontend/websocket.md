---

WebSocket — документация

Архитектура

WsClient (singleton) — низкий уровень: нативный WebSocket + переподключение  
 ↓ onStatusChange  
 useWsStore (Zustand) — публичный API: connect / disconnect / send / status
↓ запускается из
WsController (в Providers) — автоматически связывает auth-статус с WS
↓ используется в компонентах через
useWsEvent() — хук подписки на входящие события

---

Жизненный цикл соединения

Пользователь логинится
→ setSession() в auth-store
→ WsController замечает isAuthenticated = true
→ connect() берёт accessToken из auth-store
→ строит URL: ws://localhost:8000/ws?token=<accessToken>
→ wsClient.connect(url) открывает WebSocket

Соединение установлено → status = "connected"

Соединение оборвалось → status = "reconnecting"
→ попытка 1: через 1 сек
→ попытка 2: через 2 сек
→ попытка 3: через 5 сек
→ попытка 4: через 10 сек
→ попытка 5+: через 30 сек

Пользователь разлогинился / 401 в HTTP
→ clearSession() в auth-store
→ WsController замечает isAuthenticated = false
→ disconnect() — соединение закрыто, переподключение отменено
→ status = "disconnected"

---

Формат сообщений

Все сообщения — JSON с двумя полями:

{
"type": "chat.message",
"payload": { "text": "Привет", "userId": "abc-123" }
}

Фреймы, которые не парсятся как JSON, молча игнорируются.

---

Использование в компонентах

Подписка на входящие события

import { useWsEvent } from "@/shared/lib/use-ws-event";

function ChatFeed() {
useWsEvent<{ text: string; userId: string }>("chat.message", (payload) => {
console.log(payload.text);
});

    // ...

}

Хук автоматически отписывается при размонтировании компонента.

Специальный тип "\*" — получать все сообщения без фильтрации:

useWsEvent<WsMessage>("\*", (msg) => {
console.log(msg); // { type: "...", payload: ... }
});

Отправка сообщения

import { useWsStore } from "@/shared/lib/ws-store";

function ChatInput() {
const send = useWsStore((s) => s.send);

    const handleSend = () => {
      send("chat.message", { text: "Привет" });
    };

}

send отправляет только если соединение открыто (OPEN). Если соединение оборвалось — сообщение теряется (не буферизируется).

Отображение статуса соединения

import { useWsStore } from "@/shared/lib/ws-store";

function ConnectionBadge() {
const status = useWsStore((s) => s.status);

    const labels = {
      connected:     "Онлайн",
      connecting:    "Подключение...",
      reconnecting:  "Переподключение...",
      disconnected:  "Офлайн",
      error:         "Ошибка",
    };

    return <span>{labels[status]}</span>;

}

---

Статусы соединения

┌──────────────┬────────────────────────────────────────────────┐
│ Статус │ Когда возникает │
├──────────────┼────────────────────────────────────────────────┤
│ disconnected │ Начальное состояние; после явного disconnect() │
├──────────────┼────────────────────────────────────────────────┤
│ connecting │ connect() вызван, WS ещё не открыт │
├──────────────┼────────────────────────────────────────────────┤
│ connected │ onopen сработал │
├──────────────┼────────────────────────────────────────────────┤
│ reconnecting │ onclose сработал, ждём таймер переподключения │
├──────────────┼────────────────────────────────────────────────┤
│ error │ onerror сработал (обычно предшествует onclose) │
└──────────────┴────────────────────────────────────────────────┘

---

Файлы

┌────────────────────────────┬────────────────────────────────────────┐
│ Файл │ Назначение │
├────────────────────────────┼────────────────────────────────────────┤
│ shared/api/ws-client.ts │ Класс WsClient, синглтон wsClient │
├────────────────────────────┼────────────────────────────────────────┤
│ shared/lib/ws-store.ts │ Zustand-стор, публичный API │
├────────────────────────────┼────────────────────────────────────────┤
│ shared/lib/use-ws-event.ts │ Хук подписки на события │
├────────────────────────────┼────────────────────────────────────────┤
│ app/providers.tsx │ WsController — автоподключение по auth │
├────────────────────────────┼────────────────────────────────────────┤
│ shared/config/env.ts │ env.wsUrl из VITE_WS_URL │
├────────────────────────────┼────────────────────────────────────────┤
│ .env │ VITE_WS_URL=ws://localhost:8000 │
└────────────────────────────┴────────────────────────────────────────┘
