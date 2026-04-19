import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { RootLayout } from "./layout";
import { ProtectedRoute } from "./protected-route";
import { GuestRoute } from "./guest-route";
import { PublicPage } from "@/pages/public";
import { HomePage } from "@/pages/home";
import { SettingsPage } from "@/pages/settings";
import { NotFoundPage } from "@/pages/not-found";
import { LoginPage } from "@/pages/auth/login";
import { RegisterPage } from "@/pages/auth/register";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Публичная страница — доступна всем */}
        <Route path="/" element={<PublicPage />} />

        {/* Гостевые маршруты — только для неавторизованных */}
        <Route element={<GuestRoute />}>
          <Route path="auth/login" element={<LoginPage />} />
          <Route path="auth/register" element={<RegisterPage />} />
        </Route>

        {/* Защищённые маршруты — только для авторизованных */}
        <Route element={<ProtectedRoute />}>
          <Route element={<RootLayout />}>
            <Route path="home" element={<HomePage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          {/* Авторизованный пользователь на неизвестном маршруте → /home */}
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
