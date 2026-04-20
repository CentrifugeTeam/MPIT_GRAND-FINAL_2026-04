import { create } from "zustand";
import { wsClient, type WsStatus } from "@/shared/api/ws-client";
import { buildBffWebSocketUrl } from "@/shared/config/env";
import { useAuthStore } from "@/shared/lib/auth-store";

interface WsState {
  status: WsStatus;
  connect: () => void;
  disconnect: () => void;
  /** По требованию (аналитика): один WS на сессию запроса, затем `disconnect`. */
  ensureConnected: () => Promise<void>;
  send: <T>(type: string, payload: T) => void;
}

export const useWsStore = create<WsState>((set) => {
  // Пробрасываем статус из клиента в стор
  wsClient.onStatusChange = (status) => set({ status });

  return {
    status: "disconnected",

    connect: () => {
      const token = useAuthStore.getState().accessToken;
      if (!token) return;
      const url = buildBffWebSocketUrl("/api/websocket/ws", token);
      wsClient.connect(url);
    },

    ensureConnected: async () => {
      const token = useAuthStore.getState().accessToken;
      if (!token) throw new Error("Not authenticated");
      const url = buildBffWebSocketUrl("/api/websocket/ws", token);
      await wsClient.ensureOpen(url);
    },

    disconnect: () => wsClient.disconnect(),

    send: (type, payload) => wsClient.send(type, payload),
  };
});
