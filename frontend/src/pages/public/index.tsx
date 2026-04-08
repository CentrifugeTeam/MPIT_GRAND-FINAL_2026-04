import { Link } from "react-router";
import { useTranslation } from "react-i18next";

export function PublicPage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t("public.title")}</h1>
      <Link to="/auth/login">{t("public.login")}</Link>
      <Link to="/auth/register">{t("public.register")}</Link>
    </div>
  );
}
