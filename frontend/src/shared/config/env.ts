/** База для axios: пустая строка = тот же origin (Vite proxy на BFF). */
function normalizeBaseUrl(raw: string | undefined): string {
  if (raw == null || String(raw).trim() === "") {
    return "";
  }
  let u = String(raw).trim().replace(/\/+$/, "");
  if (u.endsWith("/api")) {
    u = u.slice(0, -4).replace(/\/+$/, "") || "";
  }
  return u;
}

const apiUrl = normalizeBaseUrl(import.meta.env.VITE_AUTH_SERVICE_URL as string | undefined);

function resolveWsUrl(): string {
  const explicit = (import.meta.env.VITE_WS_URL as string | undefined)?.trim();
  if (explicit) {
    return explicit.replace(/\/+$/, "");
  }
  if (apiUrl) {
    return apiUrl.replace(/^http/, "ws");
  }
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}`;
  }
  return "ws://localhost:5173";
}

/** Полный ws(s) URL для BFF (путь `/api/websocket/ws` + query token). */
export function buildBffWebSocketUrl(wsPathFromApi: string, token: string): string {
  const base =
    apiUrl ||
    (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");
  const u = new URL(base);
  const wsScheme = u.protocol === "https:" ? "wss:" : "ws:";
  const path = wsPathFromApi.startsWith("/") ? wsPathFromApi : `/${wsPathFromApi}`;
  return `${wsScheme}//${u.host}${path}?token=${encodeURIComponent(token)}`;
}

export const env = {
  apiUrl,
  wsUrl: resolveWsUrl(),
} as const;
