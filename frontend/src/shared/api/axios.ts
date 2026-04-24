import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { env } from "@/shared/config/env";
import { useAuthStore } from "@/shared/lib/auth-store";
import { authResponseSchema } from "@/shared/lib/auth-response-schema";

export const api = axios.create({
  baseURL: env.apiUrl,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

const refreshClient = axios.create({
  baseURL: env.apiUrl,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

/** Один inflight-refresh, параллельные 401 ждут тот же результат. */
let refreshPromise: Promise<string | null> | null = null;

function getRefreshedAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) {
    return Promise.resolve(null);
  }

  refreshPromise = (async () => {
    try {
      const { data } = await refreshClient.post<unknown>("/api/auth/refresh", {
        refresh_token: refreshToken,
      });
      const parsed = authResponseSchema.parse(data);
      useAuthStore.getState().setSession(parsed);
      return parsed.access_token;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

function hardLogout() {
  useAuthStore.getState().clearSession();
  if (typeof window !== "undefined") {
    window.location.href = "/";
  }
}

function isPublicAuthError(config: InternalAxiosRequestConfig) {
  const u = config.url ?? "";
  return u.includes("/api/auth/login") || u.includes("/api/auth/create");
}

// Добавляем токен в каждый запрос
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401: пробуем refresh, один раз повторяем; иначе сброс сессии
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;

    if (status !== 401 || !config) {
      return Promise.reject(error);
    }

    if (isPublicAuthError(config)) {
      return Promise.reject(error);
    }

    if (config._retry) {
      hardLogout();
      return Promise.reject(error);
    }

    const newAccess = await getRefreshedAccessToken();
    if (!newAccess) {
      hardLogout();
      return Promise.reject(error);
    }

    config._retry = true;
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${newAccess}`;
    return api.request(config);
  }
);
