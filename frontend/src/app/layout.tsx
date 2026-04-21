import { Outlet, useLocation } from "react-router";

export function RootLayout() {
  const location = useLocation();

  const isHomeRoute = location.pathname === "/home" || location.pathname.endsWith("/home");

  return (
    <div
      className={`flex min-h-screen flex-col text-foreground ${
        isHomeRoute ? "bg-[#060607]" : "bg-background"
      }`}
    >
      <main
        className={
          isHomeRoute
            ? "mx-auto flex min-h-0 w-full max-w-none flex-1 flex-col px-0 pb-0 pt-0"
            : "mx-auto max-w-6xl flex-1 p-4"
        }
      >
        <Outlet />
      </main>
    </div>
  );
}
