import { useCallback, useMemo, useState, type SyntheticEvent } from "react";
import { ListBox, Popover } from "@heroui/react";

import type { AppNotification } from "@/shared/api/notifications-api";
import { CheckIcon, CloseIcon, BellIcon } from "@/shared/ui/assets/icons";
import { FigmaSimpleTooltip } from "./figma-simple-tooltip";
import {
  getInitialsFromText,
  parseChatInvitePayload,
} from "./figma-chat-invite-payload";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

const LIST_LIMIT = 5;

/** Панель как тултип: справа от колокольчика, низ списка на уровне низа триггера. */
const NOTIFICATIONS_POPOVER_PLACEMENT = "right bottom" as const;

const NOTIFICATIONS_POPOVER_CONTENT_CLASS =
  "!min-w-0 !border-none !bg-transparent !p-0 !shadow-none outline-none overflow-visible data-[entering]:animate-none data-[exiting]:animate-none";

const NOTIFICATIONS_POPOVER_DIALOG_CLASS = "outline-none p-0";

export type FigmaSidebarNotificationsButtonProps = {
  isSidebarOpen: boolean;
  t: TFn;
  notifications: AppNotification[];
  onAccept: (inviteId: string, notificationId: string) => Promise<void>;
  onReject: (inviteId: string, notificationId: string) => Promise<void>;
  hasNotificationBadge?: boolean;
};

function stopListClickClose(e: SyntheticEvent) {
  e.stopPropagation();
  e.nativeEvent.stopImmediatePropagation();
}

export function FigmaSidebarNotificationsButton({
  isSidebarOpen,
  t,
  notifications,
  onAccept,
  onReject,
  hasNotificationBadge,
}: FigmaSidebarNotificationsButtonProps) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const showBadge = hasNotificationBadge ?? notifications.length > 0;

  const sorted = useMemo(
    () =>
      [...notifications]
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(0, LIST_LIMIT),
    [notifications],
  );

  const runAction = useCallback(
    async (
      n: AppNotification,
      kind: "accept" | "reject",
      pl: ReturnType<typeof parseChatInvitePayload>,
    ) => {
      if (!pl.invite_id) return;
      setBusyId(n.id);
      try {
        if (kind === "accept") {
          await onAccept(pl.invite_id, n.id);
        } else {
          await onReject(pl.invite_id, n.id);
        }
        setNotificationsOpen(false);
      } finally {
        setBusyId(null);
      }
    },
    [onAccept, onReject],
  );

  const triggerClassName =
    "relative flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all duration-200 outline-none data-[hovered]:bg-[#27272a]/60 data-[pressed]:scale-[0.97]";

  const trigger = (
    <Popover.Trigger
      aria-label={t("home.figma.notifications")}
      className={triggerClassName}
    >
      <span className="relative inline-flex size-4 shrink-0 items-center justify-center">
        {showBadge ? (
          <span
            className="absolute right-[1px] top-[1px] z-1 size-[5px] rounded-full bg-danger"
            aria-hidden
          />
        ) : null}
        <BellIcon className="shrink-0" width={16} height={16} />
      </span>
    </Popover.Trigger>
  );

  return (
    <Popover.Root
      isOpen={notificationsOpen}
      onOpenChange={setNotificationsOpen}
    >
      {isSidebarOpen ? (
        trigger
      ) : (
        <FigmaSimpleTooltip label={t("home.figma.notifications")} side="right">
          {trigger}
        </FigmaSimpleTooltip>
      )}

      <Popover.Content
        placement={NOTIFICATIONS_POPOVER_PLACEMENT}
        offset={10}
        shouldFlip={false}
        className={NOTIFICATIONS_POPOVER_CONTENT_CLASS}
      >
        <Popover.Dialog className={NOTIFICATIONS_POPOVER_DIALOG_CLASS}>
          <div className="flex w-[310px] max-h-[312px] flex-col overflow-hidden rounded-[26px] bg-[#121212] shadow-[0_4px_24px_rgba(0,0,0,0.35)]">
            <h2 className="shrink-0 px-[16px] pt-5 font-sans text-sm font-medium text-[#999999]">
              {t("home.figma.notifications")}
            </h2>
            {sorted.length === 0 ? (
              <p className="mt-2 px-[12px] pb-4 font-sans text-xs text-[#999999]">
                {t("home.figma.notificationsEmpty")}
              </p>
            ) : (
              <ListBox
                aria-label={t("home.figma.notifications")}
                selectionMode="none"
                items={sorted}
                className="mt-2 min-h-0 flex-1 overflow-y-auto px-[12px] pb-4 outline-none"
              >
                {(n) => {
                  if (n.type === "chat_invite") {
                    const pl = parseChatInvitePayload(n.payload ?? undefined);
                    const from = (pl.owner_email || "").trim() || n.message;
                    const initials = getInitialsFromText(
                      pl.owner_email,
                      n.title,
                    );
                    const busy = busyId === n.id;
                    const textValue = `${from} ${t("home.figma.chatInviteListSubtitle")}`;
                    return (
                      <ListBox.Item
                        key={n.id}
                        id={n.id}
                        textValue={textValue}
                        className="w-full cursor-default rounded-none border-0 border-b border-[#2a2a2a] bg-transparent px-0 py-2 shadow-none outline-none last:border-b-0 data-[focused]:bg-transparent data-[hovered]:bg-[#1a1a1a]"
                      >
                        <div
                          className="flex w-full min-w-0 items-center gap-3"
                          onClick={stopListClickClose}
                          onPointerDown={stopListClickClose}
                          role="presentation"
                        >
                          <div
                            className="flex size-11 shrink-0 items-center justify-center rounded-full bg-[#1b2b22] font-sans text-xs font-medium text-[#4caf50]"
                            aria-hidden
                          >
                            {initials}
                          </div>
                          <div className="min-w-0 flex-1 pr-2">
                            <p className="truncate font-sans text-sm font-semibold text-white">
                              {from}
                            </p>
                            <p className="truncate whitespace-nowrap font-sans text-xs text-[#888888]">
                              {t("home.figma.chatInviteListSubtitle")}
                            </p>
                          </div>
                          <div className="ml-auto flex shrink-0 items-stretch">
                            <button
                              type="button"
                              disabled={busy || !pl.invite_id}
                              onClick={(e) => {
                                stopListClickClose(e);
                                void runAction(n, "accept", pl);
                              }}
                              onPointerDown={stopListClickClose}
                              className="flex h-10 min-w-10 cursor-pointer items-center justify-center rounded-md text-white transition-colors hover:bg-white/10 disabled:opacity-40"
                              aria-label={t("home.figma.chatInviteAccept")}
                            >
                              <CheckIcon
                                className="shrink-0"
                                width={20}
                                height={20}
                              />
                            </button>
                            <div
                              className="my-1.5 w-px self-stretch bg-[#333333]"
                              aria-hidden
                            />
                            <button
                              type="button"
                              disabled={busy || !pl.invite_id}
                              onClick={(e) => {
                                stopListClickClose(e);
                                void runAction(n, "reject", pl);
                              }}
                              onPointerDown={stopListClickClose}
                              className="flex h-10 min-w-10 cursor-pointer items-center justify-center rounded-md text-white transition-colors hover:bg-white/10 disabled:opacity-40"
                              aria-label={t("home.figma.chatInviteReject")}
                            >
                              <CloseIcon
                                className="shrink-0"
                                width={20}
                                height={20}
                              />
                            </button>
                          </div>
                        </div>
                      </ListBox.Item>
                    );
                  }
                  const textValue = `${n.title} ${n.message}`;
                  return (
                    <ListBox.Item
                      key={n.id}
                      id={n.id}
                      textValue={textValue}
                      className="cursor-default rounded-none border-0 border-b border-[#2a2a2a] bg-transparent px-0 py-4 shadow-none outline-none last:border-b-0 data-[focused]:bg-transparent data-[hovered]:bg-[#1a1a1a]"
                    >
                      <p className="font-sans text-xs text-foreground">
                        {n.title}
                      </p>
                      <p className="line-clamp-2 font-sans text-xs text-[#888888]">
                        {n.message}
                      </p>
                    </ListBox.Item>
                  );
                }}
              </ListBox>
            )}
          </div>
        </Popover.Dialog>
      </Popover.Content>
    </Popover.Root>
  );
}

