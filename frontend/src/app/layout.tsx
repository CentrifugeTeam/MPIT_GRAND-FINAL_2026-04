import { Outlet, useLocation, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { Tabs } from "@heroui/react";
import type { Key } from "react";

const NAV_TABS = [
  { id: "hero", path: "/" },
  { id: "products", path: "/products" },
  { id: "about", path: "/about" },
  { id: "price", path: "/price" },
  { id: "contacts", path: "/contacts" },
] as const;

export function RootLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const selectedKey =
    NAV_TABS.find((tab) =>
      tab.path === "/"
        ? location.pathname === "/"
        : location.pathname.startsWith(tab.path),
    )?.id ?? "hero";

  const handleSelectionChange = (key: Key) => {
    const tab = NAV_TABS.find((item) => item.id === key);
    if (tab) navigate(tab.path);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <nav className="flex justify-center py-4">
        <Tabs
          selectedKey={selectedKey}
          onSelectionChange={handleSelectionChange}
        >
          <Tabs.ListContainer>
            <Tabs.List aria-label="Navigation">
              {NAV_TABS.map((tab) => (
                <Tabs.Tab key={tab.id} id={tab.id}>
                  {t(`nav.${tab.id}`)}
                  <Tabs.Indicator />
                </Tabs.Tab>
              ))}
            </Tabs.List>
          </Tabs.ListContainer>
        </Tabs>
      </nav>

      <main className="mx-auto max-w-3xl p-4">
        <Outlet />
      </main>
    </div>
  );
}
