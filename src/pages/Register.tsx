import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Lock } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import AuthLayout, { Field, ErrorMsg, SubmitButton, SwitchLink, useFormSubmit, handleSubmit } from "./AuthLayout";

export default function Register() {
  const navigate = useNavigate();
  const { registerApi } = useAuthStore();
  const form = useFormSubmit();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const usernameError = username.length > 0 && (username.length < 4 || username.length > 20)
    ? "用户名需为 4-20 位"
    : "";
  const passwordError = password.length > 0 && (password.length < 6 || password.length > 20)
    ? "密码需为 6-20 位"
    : "";
  const confirmError = confirmPassword.length > 0 && confirmPassword !== password
    ? "两次密码不一致"
    : "";

  const isFormValid = username.length >= 4 && username.length <= 20
    && password.length >= 6 && password.length <= 20
    && confirmPassword === password;

  const submit = async () => {
    await registerApi({ username, password, confirm_password: confirmPassword, real_name: "", phone: "" });
    navigate("/dashboard");
  };

  return (
    <AuthLayout
      title="创建账号"
      subtitle="注册即可享受便捷缴费服务"
      footer={<>已有账号？<SwitchLink to="/login" text="去登录" /></>}
    >
      <form onSubmit={(e) => handleSubmit(e, submit, form)} className="space-y-4">
        <Field
          label="用户名"
          value={username}
          onChange={setUsername}
          placeholder="请输入用户名 (4-20 位)"
          icon={<User className="h-4 w-4" />}
          error={usernameError}
        />
        <Field
          label="密码"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="请输入密码 (6-20 位)"
          icon={<Lock className="h-4 w-4" />}
          error={passwordError}
        />
        <Field
          label="确认密码"
          type="password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          placeholder="请再次输入密码"
          icon={<Lock className="h-4 w-4" />}
          error={confirmError}
        />
        <ErrorMsg msg={form.error} />
        <SubmitButton loading={form.loading} disabled={!isFormValid}>注册</SubmitButton>
      </form>
    </AuthLayout>
  );
}
