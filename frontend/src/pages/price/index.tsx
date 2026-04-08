import { useTranslation } from "react-i18next";

export function PricePage() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        {t("nav.price")}
      </h1>
    </div>
  );
}
