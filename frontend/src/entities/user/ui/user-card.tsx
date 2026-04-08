import { Avatar, Card } from "@heroui/react";
import { useTranslation } from "react-i18next";
import type { User } from "../model/schema";

interface UserCardProps {
  user: User;
}

export function UserCard({ user }: UserCardProps) {
  const { t, i18n } = useTranslation();

  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2);

  const formattedDate = new Intl.DateTimeFormat(i18n.language, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(user.createdAt));

  return (
    <Card className="flex-row items-center gap-4 p-4">
      <Avatar size="lg" color="accent">
        <Avatar.Image src={user.avatar} alt={user.name} />
        <Avatar.Fallback delayMs={300}>{initials}</Avatar.Fallback>
      </Avatar>
      <div className="flex flex-1 flex-col">
        <Card.Title>{user.name}</Card.Title>
        <Card.Description>
          {t("user.memberSince", { date: formattedDate })}
        </Card.Description>
      </div>
    </Card>
  );
}
