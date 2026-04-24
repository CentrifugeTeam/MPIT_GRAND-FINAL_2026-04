import { useCallback, useMemo, useState, type SyntheticEvent } from "react";
import { Dropdown } from "@heroui/react";

import type { AppNotification } from "@/shared/api/notifications-api";
import { CheckIcon, CloseIcon, BellDotIcon } from "@/shared/ui/assets/icons";
import { FIGMA_DROPDOWN_POPOVER } from "./figma-heroui-dropdown-classes";
import { FigmaSimpleTooltip } from "./figma-simple-tooltip";
import {
  getInitialsFromText,
  parseChatInvitePayload,
} from "./figma-chat-invite-payload";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

const LIST_LIMIT = 5;

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

  const panel = (
    <div
      className="flex w-[294px] flex-col overflow-hidden rounded-2xl border border-[#28282c] bg-[#0c0c0d] shadow-xl"
      style={{ height: 312 }}
    >
      <h2 className="shrink-0 px-4 pt-3 font-sans text-sm font-medium text-[#a1a1aa]">
        {t("home.figma.notifications")}
      </h2>
      <div
        className="mt-2 min-h-0 flex-1 overflow-y-auto px-2 pb-3"
        onClick={stopListClickClose}
        onPointerDown={stopListClickClose}
        role="presentation"
      >
        {sorted.length === 0 ? (
          <p className="px-2 py-2 font-sans text-xs text-[#a1a1aa]">
            {t("home.figma.notificationsEmpty")}
          </p>
        ) : (
          <ul className="flex flex-col gap-0">
            {sorted.map((n) => {
              if (n.type === "chat_invite") {
                const pl = parseChatInvitePayload(
                  n.payload ?? undefined,
                );
                const from = (pl.owner_email || "").trim() || n.message;
                const initials = getInitialsFromText(
                  pl.owner_email,
                  n.title,
                );
                const busy = busyId === n.id;
                return (
                  <li
                    key={n.id}
                    className="flex items-center gap-2 border-b border-[#28282c] py-2.5 last:border-b-0"
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
                        className="w-px self-stretch bg-[#3f3f46] my-1"
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
                  </li>
                );
              }
              return (
                <li
                  key={n.id}
                  className="border-b border-[#28282c] py-2.5 last:border-b-0"
                >
                  <p className="font-sans text-xs text-foreground">
                    {n.title}
                  </p>
                  <p className="line-clamp-2 font-sans text-[11px] text-[#a1a1aa]">
                    {n.message}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );

  const trigger = (
    <Dropdown.Trigger
      aria-label={t("home.figma.notifications")}
      className="relative flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all duration-200 outline-none data-[hovered]:bg-[#27272a]/60 data-[pressed]:scale-[0.97]"
    >
      {showBadge ? (
        <span
          className="absolute -right-0.5 -top-0.5 z-[1] inline-flex h-2.5 w-2.5 rounded-full bg-danger"
          aria-hidden
        />
      ) : null}
      <BellDotIcon className="shrink-0" width={16} height={16} />
    </Dropdown.Trigger>
  );

  return (
    <Dropdown.Root>
      {isSidebarOpen ? (
        trigger
      ) : (
        <FigmaSimpleTooltip label={t("home.figma.notifications")} side="right">
          {trigger}
        </FigmaSimpleTooltip>
      )}

      <Dropdown.Popover
        placement="top end"
        offset={8}
        className={`${FIGMA_DROPDOWN_POPOVER} !min-w-0 !border-none !bg-transparent !p-0 !shadow-none !outline-none data-[entering]:animate-none data-[exiting]:animate-none`}
        style={{ overflow: "visible" }}
      >
        {panel}
      </Dropdown.Popover>
    </Dropdown.Root>
  );
}
