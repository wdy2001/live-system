import { createBrowserRouter, RouterProvider, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import Layout from "@/components/Layout";
import { ToastProvider } from "@/components/Toast";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Payment from "@/pages/Payment";
import Records from "@/pages/Records";
import Rules from "@/pages/Rules";
import Repair from "@/pages/Repair";

function ProtectedRoute() {
  const { token } = useAuthStore();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <Layout>
      <Outlet />
    </Layout>
  );
}

function PublicOnly() {
  const { token } = useAuthStore();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/dashboard";

  if (token) {
    return <Navigate to={from} replace />;
  }

  return <Outlet />;
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    element: <PublicOnly />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/register", element: <Register /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/payment", element: <Payment /> },
      { path: "/records", element: <Records /> },
      { path: "/repair", element: <Repair /> },
    ],
  },
  {
    path: "/rules",
    element: (
      <Layout>
        <Rules />
      </Layout>
    ),
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default function App() {
  return (
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  );
}
