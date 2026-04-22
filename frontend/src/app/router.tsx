import { BrowserRouter, Routes, Route, Navigate } from 'react-router';

import { RootLayout } from '@/app/layout';
import { ProtectedRoute } from '@/app/protected-route';
import { GuestRoute } from '@/app/guest-route';
import { PublicPage } from '@/pages/public';
import { HomePage } from '@/pages/home';
import { SettingsPage } from '@/pages/settings';
import { NotFoundPage } from '@/pages/not-found';
import { LoginPage } from '@/pages/auth/login';
import { RegisterPage } from '@/pages/auth/register';
import { ReportsPage } from '@/pages/reports';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public — accessible to everyone */}
        <Route
          path='/'
          element={<PublicPage />}
        />

        {/* Guest-only routes */}
        <Route element={<GuestRoute />}>
          <Route
            path='auth/login'
            element={<LoginPage />}
          />
          <Route
            path='auth/register'
            element={<RegisterPage />}
          />
        </Route>

        {/* Protected routes — authenticated users only */}
        <Route element={<ProtectedRoute />}>
          <Route element={<RootLayout />}>
            <Route
              path='home'
              element={<HomePage />}
            />
            <Route
              path='home/:id'
              element={<HomePage />}
            />
            <Route
              path='settings'
              element={<SettingsPage />}
            />
            <Route
              path='reports'
              element={<ReportsPage />}
            />
          </Route>
          {/* Authenticated user on unknown route → /home */}
          <Route
            path='*'
            element={
              <Navigate
                to='/home'
                replace
              />
            }
          />
        </Route>

        <Route
          path='*'
          element={<NotFoundPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}
