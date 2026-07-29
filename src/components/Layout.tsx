import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Wallet, ReceiptText, Gauge, Wrench,
  LogOut, Menu, Leaf,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/dashboard", label: "工作台", icon: LayoutDashboard, end: true },
  { to: "/payment", label: "缴费中心", icon: Wallet },
  { to: "/records", label: "缴费记录", icon: ReceiptText },
  { to: "/rules", label: "计费规则", icon: Gauge },
  { to: "/repair", label: "故障报修", icon: Wrench },
];

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const SidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-6 py-7">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-forest-700 text-cream shadow-card">
          <Leaf className="h-6 w-6" />
        </div>
        <div>
          <p className="font-serif text-lg font-bold leading-tight text-forest-800">阳光社区</p>
          <p className="text-xs text-ink-muted">生活缴费系统</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all",
                isActive
                  ? "bg-forest-700 text-white shadow-card"
                  : "text-ink-soft hover:bg-forest-50 hover:text-forest-700",
              )
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-forest-50 p-4">
        <div className="mb-3 flex items-center gap-3 rounded-xl bg-forest-50/60 p-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-forest-700 font-serif font-bold text-cream">
            {user?.real_name?.[0] ?? "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">{user?.real_name}</p>
            <p className="truncate text-xs text-ink-muted">@{user?.username}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-ink-muted transition-all hover:bg-clay-50 hover:text-clay-600"
        >
          <LogOut className="h-5 w-5 shrink-0" />
          <span>退出登录</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-cream">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-forest-50 bg-white/80 backdrop-blur lg:block">
        {SidebarContent}
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink/40" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-white shadow-cardHover">
            {SidebarContent}
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-forest-50 bg-cream/90 px-4 py-3 backdrop-blur lg:hidden">
          <div className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-forest-700" />
            <span className="font-serif font-bold text-forest-800">阳光社区</span>
          </div>
          <button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-ink-soft hover:bg-forest-50">
            <Menu className="h-5 w-5" />
          </button>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PageHeader({
  title, subtitle, action,
}: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4 animate-fade-up">
      <div>
        <h1 className="font-serif text-2xl font-bold text-forest-800 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
