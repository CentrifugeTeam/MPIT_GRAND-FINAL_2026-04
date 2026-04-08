import { useTranslation } from "react-i18next";

export function ContactsPage() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        {t("nav.contacts")}
      </h1>
    </div>
  );
}

