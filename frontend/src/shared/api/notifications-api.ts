import { api } from '@/shared/api/axios';
import { env } from '@/shared/config/env';

/** EventSource needs absolute URL; при пустом VITE_ — тот же origin, что и страница (Vite proxy). */
export function getNotificationSseUrl(token: string): string {
  const base =
    env.apiUrl?.trim() ||
    (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173');
  const u = new URL('/api/notification/stream', base);
  u.searchParams.set('token', token);
  return u.toString();
}

export type AppNotification = {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  payload?: Record<string, unknown> | null;
  status: string;
  created_at: string;
};

export function createNotificationSse(token: string): EventSource {
  return new EventSource(getNotificationSseUrl(token));
}

export async function deleteNotification(userId: string, notificationId: string) {
  await api.delete(`/api/notification/${userId}/notification/${notificationId}`);
}
