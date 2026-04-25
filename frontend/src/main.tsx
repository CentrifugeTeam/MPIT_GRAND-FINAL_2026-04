import "@/shared/lib/suppress-recharts-console-warnings";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { Providers } from "@/app/providers";
import { AppRouter } from "@/app/router";

async function bootstrap() {
  if (import.meta.env.VITE_MSW_ENABLED === "true") {
    const { worker } = await import("@/shared/mocks/browser");
    await worker.start({ onUnhandledRequest: "bypass" });
  }

  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <Providers>
        <AppRouter />
      </Providers>
    </StrictMode>
  );
}

bootstrap();
