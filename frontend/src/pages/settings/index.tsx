import { Card, Switch, Select, ListBox } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useThemeStore } from "@/shared/lib/theme-store";

export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { theme, setTheme } = useThemeStore();
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        {t("settings.title")}
      </h1>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">{isDark ? "🌙" : "☀️"}</span>
            <div>
              <Card.Title>{t("settings.darkMode")}</Card.Title>
              <Card.Description>
                {theme === "system"
                  ? t("settings.darkModeSystem")
                  : isDark
                    ? t("settings.darkModeOn")
                    : t("settings.darkModeOff")}
              </Card.Description>
            </div>
          </div>
          <Switch
            isSelected={isDark}
            onChange={(selected) => setTheme(selected ? "dark" : "light")}
          >
            <Switch.Control>
              <Switch.Thumb />
            </Switch.Control>
          </Switch>
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🌐</span>
            <div>
              <Card.Title>{t("settings.language")}</Card.Title>
              <Card.Description>
                {i18n.language === "ru"
                  ? t("settings.languageRu")
                  : t("settings.languageEn")}
              </Card.Description>
            </div>
          </div>
          <Select
            aria-label={t("settings.language")}
            className="w-36"
            value={i18n.language}
            onChange={(key) => i18n.changeLanguage(String(key))}
          >
            <Select.Trigger>
              <Select.Value />
              <Select.Indicator />
            </Select.Trigger>
            <Select.Popover>
              <ListBox>
                <ListBox.Item id="ru" textValue={t("settings.languageRu")}>
                  {t("settings.languageRu")}
                  <ListBox.ItemIndicator />
                </ListBox.Item>
                <ListBox.Item id="en" textValue={t("settings.languageEn")}>
                  {t("settings.languageEn")}
                  <ListBox.ItemIndicator />
                </ListBox.Item>
              </ListBox>
            </Select.Popover>
          </Select>
        </div>
      </Card>
    </div>
  );
}
