import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Payment from "@/pages/Payment";
import Records from "@/pages/Records";
import Rules from "@/pages/Rules";
import Repair from "@/pages/Repair";

function Protected({ children }: { children: React.ReactNode }) {
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

  return <Layout>{children}</Layout>;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const init = useAuthStore((s) => s.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
        <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route path="/payment" element={<Protected><Payment /></Protected>} />
        <Route path="/records" element={<Protected><Records /></Protected>} />
        <Route path="/rules" element={<Protected><Rules /></Protected>} />
        <Route path="/repair" element={<Protected><Repair /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
