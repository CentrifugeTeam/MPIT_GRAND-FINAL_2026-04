import { BrowserRouter, Routes, Route } from "react-router";
import { RootLayout } from "./layout";
import { HomePage } from "@/pages/home";
import { ProductsPage } from "@/pages/products";
import { AboutPage } from "@/pages/about";
import { PricePage } from "@/pages/price";
import { ContactsPage } from "@/pages/contacts";
import { SettingsPage } from "@/pages/settings";
import { NotFoundPage } from "@/pages/not-found";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<HomePage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="price" element={<PricePage />} />
          <Route path="contacts" element={<ContactsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
