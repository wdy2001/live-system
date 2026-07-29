import { useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Payment from "@/pages/Payment";
import Records from "@/pages/Records";
import Rules from "@/pages/Rules";
import Repair from "@/pages/Repair";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cream">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-forest-100 border-t-forest-600" />
          <p className="text-sm text-ink-muted">加载中…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore();
  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-cream p-8 text-center">
      <h1 className="mb-4 text-6xl font-bold text-forest-700">404</h1>
      <p className="mb-8 text-lg text-ink-soft">页面不存在或已被移除</p>
      <button
        onClick={() => (window.location.href = "/dashboard")}
        className="btn-primary"
      >
        返回首页
      </button>
    </div>
  );
}

export default function App() {
  const initialize = useAuthStore((s) => s.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="payment" element={<Payment />} />
        <Route path="records" element={<Records />} />
        <Route path="rules" element={<Rules />} />
        <Route path="repair" element={<Repair />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
