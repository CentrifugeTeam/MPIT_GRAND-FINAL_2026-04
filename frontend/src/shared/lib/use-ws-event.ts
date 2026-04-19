import { useEffect } from "react";
import { wsClient } from "@/shared/api/ws-client";

/**
 * Подписка на WS-сообщения определённого типа.
 *
 * @example
 * useWsEvent<{ text: string }>("chat.message", ({ text }) => {
 *   console.log(text);
 * });
 */
export function useWsEvent<T = unknown>(
  type: string,
  handler: (payload: T) => void,
) {
  useEffect(() => {
    return wsClient.on<T>(type, handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type]);
}
