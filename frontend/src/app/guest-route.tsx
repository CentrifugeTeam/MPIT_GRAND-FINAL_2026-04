import { Navigate, Outlet } from "react-router";
import { useAuthStore } from "@/shared/lib/auth-store";

export function GuestRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());

  if (isAuthenticated) {
    return <Navigate to="/home" replace />;
  }

  return <Outlet />;
}
