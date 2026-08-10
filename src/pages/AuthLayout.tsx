import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

export default function AuthLayout({
  title, subtitle, children, footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 px-4">
      <div className="w-[400px]">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-800">生活缴费系统 · Life System</h1>
        </div>
        <div className="rounded-xl bg-white p-8 shadow-lg">
          <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          <p className="mt-1 mb-6 text-sm text-gray-500">{subtitle}</p>
          {children}
        </div>
        <p className="mt-6 text-center text-sm text-gray-500">{footer}</p>
      </div>
    </div>
  );
}

export function Field({
  label, type = "text", value, onChange, placeholder, icon, autoComplete, error,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  icon?: ReactNode;
  autoComplete?: string;
  error?: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400">
            {icon}
          </span>
        )}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={cn(
            "w-full rounded-xl border px-4 py-2.5 text-sm text-gray-800 outline-none transition",
            icon ? "pl-10" : "",
            error
              ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-100"
              : "border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          )}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}

export function ErrorMsg({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{msg}</p>;
}

export function SubmitButton({
  loading, disabled, children,
}: { loading?: boolean; disabled?: boolean; children: ReactNode }) {
  const isDisabled = loading || disabled;
  return (
    <button
      type="submit"
      disabled={isDisabled}
      className={cn(
        "mt-6 w-full rounded-xl px-5 py-2.5 text-sm font-medium text-white transition-all duration-200",
        isDisabled
          ? "cursor-not-allowed bg-blue-400 opacity-70"
          : "bg-blue-600 hover:bg-blue-700 hover:-translate-y-0.5 active:translate-y-0"
      )}
    >
      {loading ? "加载中..." : children}
    </button>
  );
}

export function SwitchLink({ to, text }: { to: string; text: ReactNode }) {
  return (
    <Link to={to} className="font-medium text-blue-600 underline-offset-2 hover:underline">
      {text}
    </Link>
  );
}

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
    state.setError(err.message || err.response?.data?.msg || "操作失败，请重试");
  }).finally(() => state.setLoading(false));
}
