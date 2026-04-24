import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthSessionPayload } from "@/shared/types/auth-session";

function decodeJwtPayloadB64u(segment: string): string {
  const pad = segment.length % 4;
  const padded = segment + (pad ? "=".repeat(4 - pad) : "");
  return atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
}

/**
 * Сохраняет `userUuid` в сторе; при старых/частичных сессиях без `userUuid` — читаем `uuid` из access JWT (auth-service).
 */
export function readUuidFromAccessToken(
  accessToken: string | null | undefined
): string | null {
  if (!accessToken) return null;
  const parts = accessToken.split(".");
  if (parts.length < 2) return null;
  try {
    const raw = JSON.parse(decodeJwtPayloadB64u(parts[1])) as {
      uuid?: string;
      sub?: string;
    };
    const u = raw.uuid ?? raw.sub;
    return typeof u === "string" && u.length > 0 ? u : null;
  } catch {
    return null;
  }
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  userUuid: string | null;
  setSession: (data: AuthSessionPayload) => void;
  clearSession: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      expiresAt: null,
      userUuid: null,
      setSession: ({ access_token, refresh_token, expires_in, user_uuid }) =>
        set({
          accessToken: access_token,
          refreshToken: refresh_token,
          expiresAt: Date.now() + expires_in * 1000,
          userUuid: user_uuid,
        }),
      clearSession: () =>
        set({ accessToken: null, refreshToken: null, expiresAt: null, userUuid: null }),
      isAuthenticated: () => {
        const { accessToken, expiresAt } = get();
        if (!accessToken) return false;
        if (expiresAt !== null && Date.now() > expiresAt) {
          set({ accessToken: null, refreshToken: null, expiresAt: null, userUuid: null });
          return false;
        }
        return true;
      },
    }),
    { name: "auth-session" }
  )
);
