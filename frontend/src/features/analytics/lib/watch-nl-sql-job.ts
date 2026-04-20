import type { NlSqlWsPayload } from "@/entities/analytics/types";
import { wsClient } from "@/shared/api/ws-client";

export type WatchNlSqlJobParams = {
  jobId: string;
  ensureWsConnected: () => Promise<void>;
  /** Сразу перед отправкой `{ type: 'watch_job' }`. */
  onBeforeWatchSent?: () => void;
  onWatchAck: () => void;
  onResult: (payload: NlSqlWsPayload) => void;
  timeoutMs: number;
  getTimeoutError: () => Error;
  /** Сохранить функцию отписки в ref родителя (`wsListenersCleanupRef.current = fn`). */
  registerListenerCleanup: (cleanup: () => void) => void;
};

/**
 * Подключение WS, watch_job, ожидание nl_sql_result по job_id; перед resolve — leave_job.
 * `disconnect` вызывает снаружи в `finally` у запуска запроса.
 */
export function watchNlSqlJobUntilResult(params: WatchNlSqlJobParams): Promise<void> {
  const {
    jobId,
    ensureWsConnected,
    onBeforeWatchSent,
    onWatchAck,
    onResult,
    timeoutMs,
    getTimeoutError,
    registerListenerCleanup,
  } = params;

  return new Promise<void>((resolve, reject) => {
    let settled = false;
    let unsubs: (() => void)[] = [];

    const tearDownListeners = () => {
      unsubs.forEach((u) => u());
      unsubs = [];
      registerListenerCleanup(() => {});
    };

    const leaveRoom = () => {
      wsClient.sendPlain({ type: "leave_job", job_id: jobId });
    };

    const timeoutId = window.setTimeout(() => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);
      tearDownListeners();
      leaveRoom();
      reject(getTimeoutError());
    }, timeoutMs);

    void (async () => {
      try {
        await ensureWsConnected();

        unsubs.push(
          wsClient.on("watch_job_ack", (payload: Record<string, unknown>) => {
            if (String(payload.job_id ?? "") !== String(jobId)) return;
            onWatchAck();
          }),
        );
        unsubs.push(
          wsClient.on("nl_sql_result", (payload: Record<string, unknown>) => {
            if (String(payload.job_id ?? "") !== String(jobId)) return;
            if (settled) return;
            settled = true;
            window.clearTimeout(timeoutId);
            const nlPayload = payload as unknown as NlSqlWsPayload;
            onResult(nlPayload);
            tearDownListeners();
            leaveRoom();
            resolve();
          }),
        );

        registerListenerCleanup(() => {
          unsubs.forEach((u) => u());
          unsubs = [];
        });

        onBeforeWatchSent?.();
        wsClient.sendPlain({ type: "watch_job", job_id: jobId });
      } catch (e) {
        if (settled) return;
        settled = true;
        window.clearTimeout(timeoutId);
        tearDownListeners();
        leaveRoom();
        reject(e instanceof Error ? e : new Error(String(e)));
      }
    })();
  });
}
