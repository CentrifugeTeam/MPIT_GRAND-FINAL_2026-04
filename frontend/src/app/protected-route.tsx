import { Navigate, Outlet } from 'react-router';
import { useAuthStore } from '@/shared/lib/auth-store';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated());

  if (!isAuthenticated) {
    return (
      <Navigate
        to='/auth/login'
        replace
      />
    );
  }

  return <Outlet />;
}
