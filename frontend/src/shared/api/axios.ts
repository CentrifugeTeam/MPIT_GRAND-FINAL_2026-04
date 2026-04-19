import axios from "axios";
import { env } from "@/shared/config/env";
import { useAuthStore } from "@/shared/lib/auth-store";

export const api = axios.create({
  baseURL: env.apiUrl,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Добавляем токен в каждый запрос
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обрабатываем 401 — чистим сессию и редиректим на публичную страницу
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearSession();
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);
