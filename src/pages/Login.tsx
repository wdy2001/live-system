import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Lock } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import AuthLayout, { Field, ErrorMsg, SubmitButton, SwitchLink, useFormSubmit, handleSubmit } from "./AuthLayout";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const form = useFormSubmit();
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("demo123");

  const submit = async () => {
    await login(username, password);
    navigate("/");
  };

  return (
    <AuthLayout
      title="欢迎回来"
      subtitle="登录账号管理你的生活缴费"
      footer={<>还没有账号？<SwitchLink to="/register" text="立即注册" /></>}
    >
      <form onSubmit={(e) => handleSubmit(e, submit, form)} className="space-y-4">
        <Field
          label="用户名"
          value={username}
          onChange={setUsername}
          placeholder="请输入用户名"
          icon={<User className="h-4 w-4" />}
          autoComplete="username"
        />
        <Field
          label="密码"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="请输入密码"
          icon={<Lock className="h-4 w-4" />}
          autoComplete="current-password"
        />
        <ErrorMsg msg={form.error} />
        <SubmitButton loading={form.loading}>登录</SubmitButton>
      </form>

      <div className="mt-5 rounded-xl bg-forest-50 px-4 py-3 text-xs text-ink-muted">
        <p className="font-medium text-forest-700">演示账号</p>
        <p className="mt-1">居民：demo / demo123</p>
        <p>管理员：admin / admin123</p>
      </div>
    </AuthLayout>
  );
}
