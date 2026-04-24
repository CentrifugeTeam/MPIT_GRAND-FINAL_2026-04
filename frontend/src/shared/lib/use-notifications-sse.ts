import { useCallback, useEffect, useState } from 'react';

import { type AppNotification } from '@/shared/api/notifications-api';
import {
  forceReconnectNotificationSse,
  subscribeNotificationSse,
} from '@/shared/lib/notification-sse-broadcast';

type UseNotificationsSseResult = {
  notifications: AppNotification[];
  /** false пока нет open или после ошибки до переподключения */
  sseConnected: boolean;
  refresh: () => Promise<void>;
};

/**
 * Список уведомлений только через SSE (первый кадр — из потока при открытии).
 * Токен в query — EventSource не умеет Authorization header.
 */
export function useNotificationsSse(accessToken: string | null): UseNotificationsSseResult {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [sseConnected, setSseConnected] = useState(false);

  const refresh = useCallback(async () => {
    forceReconnectNotificationSse();
  }, []);

  useEffect(() => {
    if (!accessToken) {
      const t = requestAnimationFrame(() => {
        setSseConnected(false);
        setNotifications([]);
      });
      return () => cancelAnimationFrame(t);
    }

    return subscribeNotificationSse(
      accessToken,
      (rows) => {
        setNotifications(rows);
      },
      (c) => {
        setSseConnected(c);
      },
    );
  }, [accessToken]);

  return { notifications, sseConnected, refresh };
}
