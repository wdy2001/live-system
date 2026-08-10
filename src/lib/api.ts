import axios from "axios";
import { useAuthStore } from "@/store/auth";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const storeToken = useAuthStore.getState().token;
  const localToken = localStorage.getItem("auth-storage");
  let token = storeToken;
  if (!token && localToken) {
    try {
      const parsed = JSON.parse(localToken);
      token = parsed.state?.token;
    } catch {
      token = null;
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    const msg = error.response?.data?.msg || error.message || "请求失败";
    console.error("[API Error]:", msg, error);
    return Promise.reject(new Error(msg));
  },
);

export default api;
