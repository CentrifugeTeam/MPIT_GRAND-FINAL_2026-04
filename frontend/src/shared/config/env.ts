const apiUrl = import.meta.env.VITE_AUTH_SERVICE_URL as string;

export const env = {
  apiUrl,
  wsUrl: (import.meta.env.VITE_WS_URL as string | undefined) ?? apiUrl.replace(/^http/, "ws"),
} as const;
