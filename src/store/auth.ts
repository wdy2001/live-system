import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import api from "@/lib/api";

interface AuthState {
  token: string | null;
  user: User | null;
  login: (payload: { token: string; user: User }) => void;
  logout: () => void;
  register: (payload: { token: string; user: User }) => void;
  loginApi: (username: string, password: string) => Promise<void>;
  registerApi: (payload: {
    username: string;
    password: string;
    real_name: string;
    phone: string;
  }) => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,

      login: ({ token, user }) => {
        set({ token, user });
      },

      logout: () => {
        set({ token: null, user: null });
      },

      register: ({ token, user }) => {
        set({ token, user });
      },

      loginApi: async (username, password) => {
        const { data } = await api.post("/auth/login", { username, password });
        set({ token: data.access_token, user: data.user });
      },

      registerApi: async (payload) => {
        const { data } = await api.post("/auth/register", payload);
        set({ token: data.access_token, user: data.user });
      },
    }),
    {
      name: "auth-storage",
    },
  ),
);
