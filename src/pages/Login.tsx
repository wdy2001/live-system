import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { User, Lock } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import AuthLayout, { Field, ErrorMsg, SubmitButton, SwitchLink, useFormSubmit, handleSubmit } from "./AuthLayout";

export default function Login() {
  const navigate = useNavigate();
  const { loginApi } = useAuthStore();
  const form = useFormSubmit();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const usernameError = username.length > 0 && (username.length < 4 || username.length > 20)
    ? "用户名需为 4-20 位"
    : "";
  const passwordError = password.length > 0 && (password.length < 6 || password.length > 20)
    ? "密码需为 6-20 位"
    : "";

  const isFormValid = username.length >= 4 && username.length <= 20
    && password.length >= 6 && password.length <= 20;

  const submit = async () => {
    await loginApi(username, password);
    setSuccessMsg("登录成功");
    setTimeout(() => {
      navigate("/dashboard");
    }, 500);
  };

  useEffect(() => {
    if (successMsg) {
      const t = setTimeout(() => setSuccessMsg(""), 2000);
      return () => clearTimeout(t);
    }
  }, [successMsg]);

  return (
    <AuthLayout
      title="欢迎回来"
      subtitle="登录账号管理你的生活缴费"
      footer={<>没有账号？<SwitchLink to="/register" text="去注册" /></>}
    >
      <form onSubmit={(e) => handleSubmit(e, submit, form)} className="space-y-4">
        <Field
          label="用户名"
          value={username}
          onChange={setUsername}
          placeholder="请输入用户名 (4-20 位)"
          icon={<User className="h-4 w-4" />}
          autoComplete="username"
          error={usernameError}
        />
        <Field
          label="密码"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="请输入密码 (6-20 位)"
          icon={<Lock className="h-4 w-4" />}
          autoComplete="current-password"
          error={passwordError}
        />
        {successMsg && (
          <p className="mt-4 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-600">{successMsg}</p>
        )}
        <ErrorMsg msg={form.error} />
        <SubmitButton loading={form.loading} disabled={!isFormValid}>登录</SubmitButton>
      </form>
    </AuthLayout>
  );
}
