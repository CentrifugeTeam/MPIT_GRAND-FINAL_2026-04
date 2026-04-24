import type { ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toast } from "@heroui/react";

import { queryClient } from "@/shared/lib/query-client";
import { downloadQueue } from "@/shared/lib/download-queue";
import "@/shared/lib/i18n";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <Toast.Provider />
      <Toast.Provider placement="top" queue={downloadQueue} />
      {children}
    </QueryClientProvider>
  );
}
