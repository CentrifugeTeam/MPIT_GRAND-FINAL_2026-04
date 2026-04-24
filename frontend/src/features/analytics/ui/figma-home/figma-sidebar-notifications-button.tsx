import { useCallback, useMemo, useState, type SyntheticEvent } from "react";
import { ListBox, Popover } from "@heroui/react";

import type { AppNotification } from "@/shared/api/notifications-api";
import { CheckIcon, CloseIcon, BellDotIcon } from "@/shared/ui/assets/icons";
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
      {showBadge ? (
        <span
          className="absolute -right-0.5 -top-0.5 z-[1] inline-flex h-2.5 w-2.5 rounded-full bg-danger"
          aria-hidden
        />
      ) : null}
      <BellDotIcon className="shrink-0" width={16} height={16} />
    </Popover.Trigger>
  );

  return (
    <Popover.Root>
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
          <div
            className="flex w-[294px] flex-col overflow-hidden rounded-2xl border border-[#28282c] bg-[#0c0c0d] shadow-[0_4px_24px_rgba(0,0,0,0.35)]"
            style={{ height: 312 }}
          >
            <h2 className="shrink-0 px-4 pt-3 font-sans text-sm font-medium text-[#a1a1aa]">
              {t("home.figma.notifications")}
            </h2>
            {sorted.length === 0 ? (
              <p className="mt-2 px-4 pb-3 font-sans text-xs text-[#a1a1aa]">
                {t("home.figma.notificationsEmpty")}
              </p>
            ) : (
              <ListBox
                aria-label={t("home.figma.notifications")}
                selectionMode="none"
                items={sorted}
                className="mt-2 min-h-0 flex-1 overflow-y-auto px-2 pb-3 outline-none"
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
                        className="cursor-default rounded-none border-0 border-b border-[#28282c] bg-transparent px-0 py-2.5 shadow-none outline-none last:border-b-0 data-[focused]:bg-transparent data-[hovered]:bg-[#121214]"
                      >
                        <div
                          className="flex items-center gap-2"
                          onClick={stopListClickClose}
                          onPointerDown={stopListClickClose}
                          role="presentation"
                        >
                          <div
                            className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[#0f2e1f] text-[11px] font-medium text-[#4ade80]"
                            aria-hidden
                          >
                            {initials}
                          </div>
                          <div className="min-w-0 flex-1 pr-1">
                            <p className="truncate font-sans text-sm font-medium text-[#fcfcfc]">
                              {from}
                            </p>
                            <p className="font-sans text-[11px] text-[#a1a1aa]">
                              {t("home.figma.chatInviteListSubtitle")}
                            </p>
                          </div>
                          <div className="flex shrink-0 items-stretch">
                            <button
                              type="button"
                              disabled={busy || !pl.invite_id}
                              onClick={(e) => {
                                stopListClickClose(e);
                                void runAction(n, "accept", pl);
                              }}
                              onPointerDown={stopListClickClose}
                              className="flex size-8 cursor-pointer items-center justify-center rounded-l-lg text-[#fcfcfc] transition-colors hover:bg-[#27272a]/60 disabled:opacity-40"
                              aria-label={t("home.figma.chatInviteAccept")}
                            >
                              <CheckIcon
                                className="shrink-0"
                                width={16}
                                height={16}
                              />
                            </button>
                            <div
                              className="my-1 w-px self-stretch bg-[#3f3f46]"
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
                              className="flex size-8 cursor-pointer items-center justify-center rounded-r-lg text-[#fcfcfc] transition-colors hover:bg-[#27272a]/60 disabled:opacity-40"
                              aria-label={t("home.figma.chatInviteReject")}
                            >
                              <CloseIcon
                                className="shrink-0"
                                width={16}
                                height={16}
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
                      className="cursor-default rounded-none border-0 border-b border-[#28282c] bg-transparent px-0 py-2.5 shadow-none outline-none last:border-b-0 data-[focused]:bg-transparent data-[hovered]:bg-[#121214]"
                    >
                      <p className="font-sans text-xs text-foreground">{n.title}</p>
                      <p className="line-clamp-2 font-sans text-[11px] text-[#a1a1aa]">
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
