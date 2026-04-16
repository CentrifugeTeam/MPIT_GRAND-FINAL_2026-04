import { create } from "zustand";
import { persist } from "zustand/middleware";

const TOKEN_TTL_MS = 24 * 60 * 60 * 1000; // 24 часа

interface AuthState {
  token: string | null;
  expiresAt: number | null;
  setToken: (token: string) => void;
  clearToken: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      expiresAt: null,
      setToken: (token) => set({ token, expiresAt: Date.now() + TOKEN_TTL_MS }),
      clearToken: () => set({ token: null, expiresAt: null }),
      isAuthenticated: () => {
        const { token, expiresAt } = get();
        if (!token) return false;
        if (expiresAt !== null && Date.now() > expiresAt) {
          set({ token: null, expiresAt: null });
          return false;
        }
        return true;
      },
    }),
    { name: "auth-token" }
  )
);
