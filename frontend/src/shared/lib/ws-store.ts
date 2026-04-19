import { create } from "zustand";
import { wsClient, type WsStatus } from "@/shared/api/ws-client";
import { env } from "@/shared/config/env";
import { useAuthStore } from "@/shared/lib/auth-store";

interface WsState {
  status: WsStatus;
  connect: () => void;
  disconnect: () => void;
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
      const url = `${env.wsUrl}/ws?token=${encodeURIComponent(token)}`;
      wsClient.connect(url);
    },

    disconnect: () => wsClient.disconnect(),

    send: (type, payload) => wsClient.send(type, payload),
  };
});
