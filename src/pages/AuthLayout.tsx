import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Leaf, Zap, Droplets, Flame } from "lucide-react";

/** 登录/注册共用的品牌背景布局 */
export default function AuthLayout({
  title, subtitle, children, footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-forest-800 px-4 py-10">
      {/* 装饰光斑 */}
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-forest-600/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-20 h-96 w-96 rounded-full bg-energy-600/20 blur-3xl" />
      <div className="pointer-events-none absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-aqua-500/10 blur-3xl" />

      {/* 漂浮图标 */}
      <Zap className="pointer-events-none absolute left-[12%] top-[20%] h-8 w-8 text-energy-400/30" />
      <Droplets className="pointer-events-none absolute right-[14%] top-[28%] h-7 w-7 text-aqua-400/30" />
      <Flame className="pointer-events-none absolute bottom-[18%] left-[18%] h-7 w-7 text-clay-400/30" />

      <div className="relative w-full max-w-md animate-scale-in">
        {/* 品牌头 */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-cream shadow-cardHover">
            <Leaf className="h-8 w-8 text-forest-700" />
          </div>
          <h1 className="font-serif text-2xl font-bold text-cream">阳光社区</h1>
          <p className="mt-1 text-sm text-forest-200">一站式生活缴费服务平台</p>
        </div>

        {/* 表单卡片 */}
        <div className="rounded-2xl bg-cream p-8 shadow-cardHover">
          <h2 className="font-serif text-xl font-bold text-forest-800">{title}</h2>
          <p className="mt-1 mb-6 text-sm text-ink-muted">{subtitle}</p>
          {children}
        </div>

        <p className="mt-6 text-center text-sm text-forest-200">{footer}</p>
      </div>
    </div>
  );
}

/** 通用表单字段 */
export function Field({
  label, type = "text", value, onChange, placeholder, icon, autoComplete,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  icon?: ReactNode;
  autoComplete?: string;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-muted">
            {icon}
          </span>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={icon ? "input pl-10" : "input"}
        />
      </div>
    </div>
  );
}

/** 通用错误提示 */
export function ErrorMsg({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p className="mt-4 rounded-lg bg-clay-50 px-3 py-2 text-sm text-clay-600">{msg}</p>;
}

export function SubmitButton({
  loading, children,
}: { loading: boolean; children: ReactNode }) {
  return (
    <button type="submit" disabled={loading} className="btn-primary mt-6 w-full">
      {loading ? "处理中..." : children}
    </button>
  );
}

export function SwitchLink({ to, text }: { to: string; text: ReactNode }) {
  return (
    <Link to={to} className="font-medium text-forest-600 underline-offset-2 hover:underline">
      {text}
    </Link>
  );
}

/** 通用表单提交 hook */
export function useFormSubmit() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  return { loading, setLoading, error, setError };
}

export type SubmitFn = ReturnType<typeof useFormSubmit>;

export function handleSubmit(
  e: FormEvent,
  fn: () => Promise<void>,
  state: SubmitFn,
) {
  e.preventDefault();
  state.setError("");
  state.setLoading(true);
  fn().catch((err) => {
    state.setError(err.response?.data?.msg || "操作失败，请重试");
  }).finally(() => state.setLoading(false));
}
