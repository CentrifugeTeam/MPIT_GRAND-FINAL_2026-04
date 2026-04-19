import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthResponse } from "@/entities/auth/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  userUuid: string | null;
  setSession: (data: AuthResponse) => void;
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
