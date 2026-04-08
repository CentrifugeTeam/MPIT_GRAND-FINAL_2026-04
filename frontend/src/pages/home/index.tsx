import { Alert, Spinner } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useUsers, UserCard } from "@/entities/user";

export function HomePage() {
  const { t } = useTranslation();
  const { data: users, isLoading, error } = useUsers();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold text-foreground">
        {t("home.title")}
      </h1>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <Alert status="danger">
          <Alert.Content>
            <Alert.Title>{t("home.error")}</Alert.Title>
            <Alert.Description>{error.message}</Alert.Description>
          </Alert.Content>
        </Alert>
      )}

      {users && (
        <div className="flex flex-col gap-3">
          {users.map((user) => (
            <UserCard key={user.id} user={user} />
          ))}
        </div>
      )}
    </div>
  );
}
