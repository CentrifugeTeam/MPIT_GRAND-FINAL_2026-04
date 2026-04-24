import { createNotificationSse, type AppNotification } from '@/shared/api/notifications-api';

type Sub = {
  onNotif: (n: AppNotification[]) => void;
  onConnect: (c: boolean) => void;
};

const subs = new Set<Sub>();
let es: EventSource | null = null;
let currentToken: string | null = null;
let retryTimer: ReturnType<typeof setTimeout> | null = null;
let retryCount = 0;

function connectNow() {
  if (!currentToken) {
    return;
  }
  es?.close();
  try {
    es = createNotificationSse(currentToken);
    es.addEventListener('open', () => {
      retryCount = 0;
      for (const s of subs) {
        s.onConnect(true);
      }
    });
    es.addEventListener('notifications', (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data) as { notifications?: AppNotification[] };
        if (!Array.isArray(parsed.notifications)) {
          return;
        }
        for (const s of subs) {
          s.onNotif(parsed.notifications);
        }
      } catch {
        // ignore
      }
    });
    es.onerror = () => {
      for (const s of subs) {
        s.onConnect(false);
      }
      es?.close();
      if (subs.size === 0) {
        return;
      }
      const delay = Math.min(30_000, 1500 * 2 ** retryCount);
      retryCount += 1;
      if (retryTimer) {
        clearTimeout(retryTimer);
      }
      retryTimer = setTimeout(connectNow, delay);
    };
  } catch {
    for (const s of subs) {
      s.onConnect(false);
    }
    if (retryTimer) {
      clearTimeout(retryTimer);
    }
    retryTimer = setTimeout(connectNow, 3000);
  }
}

/** Переподключить поток: сервер снова отдаёт полный список в первом `notifications`. */
export function forceReconnectNotificationSse(): void {
  if (!currentToken || subs.size === 0) {
    return;
  }
  if (retryTimer) {
    clearTimeout(retryTimer);
    retryTimer = null;
  }
  retryCount = 0;
  es?.close();
  es = null;
  connectNow();
}

/**
 * Один EventSource на accessToken: меньше дублей при React StrictMode и remount.
 */
export function subscribeNotificationSse(
  token: string,
  onNotif: (n: AppNotification[]) => void,
  onConnect: (c: boolean) => void,
): () => void {
  const sub: Sub = { onNotif, onConnect };
  subs.add(sub);
  if (currentToken !== token) {
    currentToken = token;
    if (retryTimer) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    retryCount = 0;
    connectNow();
  } else if (!es || es.readyState === EventSource.CLOSED) {
    if (retryTimer) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    connectNow();
  } else if (es.readyState === EventSource.OPEN) {
    sub.onConnect(true);
  }
  return () => {
    subs.delete(sub);
    if (subs.size === 0) {
      if (retryTimer) {
        clearTimeout(retryTimer);
        retryTimer = null;
      }
      es?.close();
      es = null;
      currentToken = null;
      retryCount = 0;
    }
  };
}
