import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

// 请求拦截：附带 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("life_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：统一错误处理
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("life_token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
