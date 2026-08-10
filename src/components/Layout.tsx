import { type ReactNode } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import {
  Home, CreditCard, FileText, Settings, Wrench,
  LogOut,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/dashboard", label: "工作台", icon: Home, end: true },
  { to: "/payment", label: "缴费中心", icon: CreditCard },
  { to: "/records", label: "缴费记录", icon: FileText },
  { to: "/rules", label: "计费规则", icon: Settings },
  { to: "/repair", label: "故障报修", icon: Wrench },
];

const PAGE_TITLE: Record<string, string> = {
  "/dashboard": "工作台",
  "/payment": "缴费中心",
  "/records": "缴费记录",
  "/rules": "计费规则",
  "/repair": "故障报修",
};

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const currentPageTitle = PAGE_TITLE[location.pathname] || "工作台";

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-slate-50 min-h-screen flex flex-col">
        <div className="px-6 py-7">
          <h1 className="text-xl font-bold text-gray-800">生活缴费系统</h1>
          <p className="text-xs text-gray-500 mt-1">Life System</p>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-4 py-3 text-sm transition-all border-l-4",
                  isActive
                    ? "bg-white border-blue-500 font-bold text-gray-800"
                    : "border-transparent text-gray-600 hover:bg-white/60"
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-h-screen">
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">{currentPageTitle}</h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700">{user?.username}</span>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 transition"
            >
              <LogOut className="h-4 w-4" />
              退出登录
            </button>
          </div>
        </header>

        <main className="flex-1 p-8 bg-gray-50">
          {children}
        </main>
      </div>
    </div>
  );
}

export function PageHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-800 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
