import { create } from "zustand";
import type { User } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  loading: boolean;
  init: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (payload: {
    username: string;
    password: string;
    real_name: string;
    phone: string;
  }) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,

  init: async () => {
    const token = localStorage.getItem("life_token");
    if (!token) {
      set({ loading: false, user: null });
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data.user, loading: false });
    } catch {
      localStorage.removeItem("life_token");
      set({ user: null, loading: false });
    }
  },

  login: async (username, password) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("life_token", data.token);
    set({ user: data.user });
  },

  register: async (payload) => {
    const { data } = await api.post("/auth/register", payload);
    localStorage.setItem("life_token", data.token);
    set({ user: data.user });
  },

  logout: () => {
    localStorage.removeItem("life_token");
    set({ user: null });
  },
}));
