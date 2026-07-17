import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Lock, Phone, IdCard } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import AuthLayout, { Field, ErrorMsg, SubmitButton, SwitchLink, useFormSubmit, handleSubmit } from "./AuthLayout";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuthStore();
  const form = useFormSubmit();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [realName, setRealName] = useState("");
  const [phone, setPhone] = useState("");

  const submit = async () => {
    await register({ username, password, real_name: realName, phone });
    navigate("/");
  };

  return (
    <AuthLayout
      title="创建账号"
      subtitle="注册即可享受便捷缴费服务"
      footer={<>已有账号？<SwitchLink to="/login" text="返回登录" /></>}
    >
      <form onSubmit={(e) => handleSubmit(e, submit, form)} className="space-y-4">
        <Field
          label="用户名"
          value={username}
          onChange={setUsername}
          placeholder="3-50 位字符"
          icon={<User className="h-4 w-4" />}
        />
        <Field
          label="密码"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="至少 6 位"
          icon={<Lock className="h-4 w-4" />}
        />
        <Field
          label="真实姓名"
          value={realName}
          onChange={setRealName}
          placeholder="便于登记缴费户号"
          icon={<IdCard className="h-4 w-4" />}
        />
        <Field
          label="手机号"
          value={phone}
          onChange={setPhone}
          placeholder="用于接收缴费提醒"
          icon={<Phone className="h-4 w-4" />}
        />
        <ErrorMsg msg={form.error} />
        <SubmitButton loading={form.loading}>注册并登录</SubmitButton>
      </form>
    </AuthLayout>
  );
}
