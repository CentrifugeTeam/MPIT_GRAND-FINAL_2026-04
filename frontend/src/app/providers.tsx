import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toast } from "@heroui/react";
import { queryClient } from "@/shared/lib/query-client";
import { useAuthStore } from "@/shared/lib/auth-store";
import { useWsStore } from "@/shared/lib/ws-store";
import "@/shared/lib/i18n";

/** Следит за auth-статусом и управляет WS-соединением. */
function WsController() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  const connect = useWsStore((s) => s.connect);
  const disconnect = useWsStore((s) => s.disconnect);

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    } else {
      disconnect();
    }
  }, [isAuthenticated, connect, disconnect]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <Toast.Provider />
      <WsController />
      {children}
    </QueryClientProvider>
  );
}
