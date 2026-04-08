import { BrowserRouter, Routes, Route } from "react-router";
import { RootLayout } from "./layout";
import { ProtectedRoute } from "./protected-route";
import { GuestRoute } from "./guest-route";
import { PublicPage } from "@/pages/public";
import { HomePage } from "@/pages/home";
import { ProductsPage } from "@/pages/products";
import { AboutPage } from "@/pages/about";
import { PricePage } from "@/pages/price";
import { ContactsPage } from "@/pages/contacts";
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
            <Route path="products" element={<ProductsPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="price" element={<PricePage />} />
            <Route path="contacts" element={<ContactsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
