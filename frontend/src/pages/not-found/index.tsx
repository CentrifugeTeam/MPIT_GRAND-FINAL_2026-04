import { Link } from "react-router";
import { useTranslation } from "react-i18next";

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 py-20">
      <h1 className="text-xl font-bold text-foreground">{t("notFound.title")}</h1>
      <Link to="/" className="text-accent hover:underline">
        {t("notFound.goHome")}
      </Link>
    </div>
  );
}
