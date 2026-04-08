import { create } from "zustand";

interface AppState {
  // Add your state here
}

export const useAppStore = create<AppState>()(() => ({
  // Add your initial state here
}));
