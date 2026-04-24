import type { RefObject } from "react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useMemo,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { motion } from "motion/react";

import type { AppNotification } from "@/shared/api/notifications-api";
import { CheckIcon, CloseIcon } from "@/shared/ui/assets/icons";
import {
  getInitialsFromText,
  parseChatInvitePayload,
} from "./figma-chat-invite-payload";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

const LIST_LIMIT = 5;
const GAP = 8;
const VIEWPORT_MARGIN = 8;
const TOOLTIP_Z = 50_000;

type Coords = { top: number; left: number; transform: string };

type Side = "bottom" | "top" | "left" | "right";

function computeCoords(rect: DOMRect, side: Side): Coords {
  switch (side) {
    case "top":
      return {
        top: rect.top - GAP,
        left: rect.left + rect.width / 2,
        transform: "translate(-50%, -100%)",
      };
    case "left":
      return {
        top: rect.top + rect.height / 2,
        left: rect.left - GAP,
        transform: "translate(-100%, -50%)",
      };
    case "right":
      return {
        top: rect.top + rect.height / 2,
        left: rect.right + GAP,
        transform: "translateY(-50%)",
      };
    case "bottom":
    default:
      return {
        top: rect.bottom + GAP,
        left: rect.left + rect.width / 2,
        transform: "translateX(-50%)",
      };
  }
}

export type FigmaNotificationsPanelTooltipProps = {
  t: TFn;
  notifications: AppNotification[];
  onClose: () => void;
  onAccept: (inviteId: string, notificationId: string) => Promise<void>;
  onReject: (inviteId: string, notificationId: string) => Promise<void>;
  /** Элемент колокольчика — панель позиционируется как у `FigmaSimpleTooltip`, сбоку от сайдбара. */
  anchorRef: RefObject<HTMLElement | null>;
  side?: Side;
};

export function FigmaNotificationsPanelTooltip({
  t,
  notifications,
  onClose,
  onAccept,
  onReject,
  anchorRef,
  side = "right",
}: FigmaNotificationsPanelTooltipProps) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [coords, setCoords] = useState<Coords | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const sorted = useMemo(
    () =>
      [...notifications]
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(0, LIST_LIMIT),
    [notifications],
  );

  const updatePosition = useCallback(() => {
    const el = anchorRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setCoords(computeCoords(rect, side));
  }, [anchorRef, side]);

  useLayoutEffect(() => {
    updatePosition();
  }, [updatePosition, sorted.length, notifications]);

  useEffect(() => {
    const onScrollOrResize = () => updatePosition();
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [updatePosition]);

  useLayoutEffect(() => {
    const tip = panelRef.current;
    if (!tip || !coords) return;
    if (coords.transform === "none") return;
    const tipRect = tip.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let newLeft = tipRect.left;
    let newTop = tipRect.top;
    let changed = false;

    if (tipRect.right > vw - VIEWPORT_MARGIN) {
      newLeft = vw - VIEWPORT_MARGIN - tipRect.width;
      changed = true;
    } else if (tipRect.left < VIEWPORT_MARGIN) {
      newLeft = VIEWPORT_MARGIN;
      changed = true;
    }

    if (tipRect.bottom > vh - VIEWPORT_MARGIN) {
      newTop = vh - VIEWPORT_MARGIN - tipRect.height;
      changed = true;
    } else if (tipRect.top < VIEWPORT_MARGIN) {
      newTop = VIEWPORT_MARGIN;
      changed = true;
    }

    if (changed) {
      setCoords({ top: newTop, left: newLeft, transform: "none" });
    }
  }, [coords]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busyId) onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose, busyId]);

  useEffect(() => {
    const onPointerDown = (e: PointerEvent) => {
      const node = e.target as Node;
      if (panelRef.current?.contains(node)) return;
      if (anchorRef.current?.contains(node)) return;
      if (!busyId) onClose();
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [onClose, busyId, anchorRef]);

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

  if (!coords || typeof document === "undefined") return null;

  return createPortal(
    <motion.div
      ref={panelRef}
      role="dialog"
      aria-label={t("home.figma.notifications")}
      style={{
        position: "fixed",
        top: coords.top,
        left: coords.left,
        transform: coords.transform,
        zIndex: TOOLTIP_Z,
        height: 312,
      }}
      className="pointer-events-auto flex w-[294px] max-h-[90vh] flex-col overflow-hidden rounded-2xl border border-[#28282c] bg-[#0c0c0d] shadow-[0_4px_24px_rgba(0,0,0,0.35)]"
      initial={{ scale: 0.97, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.97, opacity: 0 }}
      transition={{ duration: 0.15 }}
      onClick={(e) => e.stopPropagation()}
    >
      <h2 className="shrink-0 px-4 pt-3 font-sans text-sm font-medium text-[#a1a1aa]">
        {t("home.figma.notifications")}
      </h2>
      <div className="mt-2 min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {sorted.length === 0 ? (
          <p className="px-2 py-2 font-sans text-xs text-[#a1a1aa]">
            {t("home.figma.notificationsEmpty")}
          </p>
        ) : (
          <ul className="flex flex-col gap-0">
            {sorted.map((n) => {
              if (n.type === "chat_invite") {
                const pl = parseChatInvitePayload(n.payload ?? undefined);
                const from =
                  (pl.owner_email || "").trim() || n.message;
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
                        onClick={() => void runAction(n, "accept", pl)}
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
                        onClick={() => void runAction(n, "reject", pl)}
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
                  <p className="font-sans text-xs text-foreground">{n.title}</p>
                  <p className="line-clamp-2 font-sans text-[11px] text-[#a1a1aa]">
                    {n.message}
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </motion.div>,
    document.body,
  );
}
