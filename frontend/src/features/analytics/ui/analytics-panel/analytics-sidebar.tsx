import type { RefObject } from "react";
import { Dropdown } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";

import { formatChatTime } from "../../lib/format-chat-time";

export type AnalyticsSidebarProps = {
  entries: AnalyticsChatEntry[];
  titles: Record<string, string>;
  activeId: string | null;
  editingRowId: string | null;
  renameDraft: string;
  renameFieldFocused: boolean;
  renameInputRef: RefObject<HTMLInputElement | null>;
  historyBusy: boolean;
  onRenameDraft: (v: string) => void;
  onRenameFocus: (focused: boolean) => void;
  onCommitRename: () => void;
  onCancelRename: () => void;
  onSelectEntry: (id: string) => void;
  onStartNewChat: () => void;
  onLoadHistory: () => void;
  onConfirmDeleteAll: () => void;
  onStartEditingRow: (e: AnalyticsChatEntry) => void;
  onConfirmDeleteOne: (jobId: string) => void;
  t: (key: string) => string;
};

export function AnalyticsSidebar({
  entries,
  titles,
  activeId,
  editingRowId,
  renameDraft,
  renameFieldFocused,
  renameInputRef,
  historyBusy,
  onRenameDraft,
  onRenameFocus,
  onCommitRename,
  onCancelRename,
  onSelectEntry,
  onStartNewChat,
  onLoadHistory,
  onConfirmDeleteAll,
  onStartEditingRow,
  onConfirmDeleteOne,
  t,
}: AnalyticsSidebarProps) {
  return (
    <aside className="border-border bg-surface-secondary/40 w-full shrink-0 lg:w-80 lg:max-w-[min(100%,20rem)] lg:rounded-2xl lg:border lg:p-3">
      <div className="mb-3 flex items-center justify-between gap-2 px-1">
        <h2 className="text-foreground text-sm font-semibold">
          {t("home.analytics.sidebarTitle")}
        </h2>
        <Dropdown.Root>
          <Dropdown.Trigger
            aria-label={t("home.analytics.sidebarMenuAria")}
            className="inline-flex h-8 w-8 min-w-8 shrink-0 items-center justify-center rounded-lg text-muted hover:bg-default hover:text-foreground"
          >
            <Icon icon="mdi:dots-vertical" width={18} />
          </Dropdown.Trigger>
          <Dropdown.Popover placement="bottom end">
            <Dropdown.Menu>
              <Dropdown.Item
                textValue={t("home.analytics.newQuestion")}
                onAction={onStartNewChat}
              >
                <span className="flex items-center gap-2">
                  <Icon icon="mdi:message-plus-outline" width={18} />
                  {t("home.analytics.newQuestion")}
                </span>
              </Dropdown.Item>
              <Dropdown.Item
                textValue={t("home.analytics.refreshHistory")}
                onAction={() => {
                  if (!historyBusy) onLoadHistory();
                }}
              >
                <span className="flex items-center gap-2">
                  <Icon
                    icon={historyBusy ? "mdi:loading" : "mdi:refresh"}
                    className={historyBusy ? "animate-spin" : undefined}
                    width={18}
                  />
                  {historyBusy
                    ? t("home.analytics.historyLoading")
                    : t("home.analytics.refreshHistory")}
                </span>
              </Dropdown.Item>
              <Dropdown.Item
                textValue={t("home.analytics.deleteAllHistory")}
                onAction={() => {
                  if (entries.length > 0) void onConfirmDeleteAll();
                }}
              >
                <span className="flex items-center gap-2 text-danger">
                  <Icon icon="mdi:delete-sweep-outline" width={18} />
                  {t("home.analytics.deleteAllHistory")}
                </span>
              </Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown.Popover>
        </Dropdown.Root>
      </div>
      <div className="flex max-h-[min(520px,55vh)] flex-col gap-2 overflow-y-auto lg:max-h-[calc(100vh-220px)]">
        {entries.length === 0 && (
          <p className="text-muted px-2 py-4 text-xs">{t("home.analytics.sidebarEmpty")}</p>
        )}
        {entries.map((e) => {
          const rowLabel = titles[e.id] ?? e.question;
          const isEditing = editingRowId === e.id;
          return (
            <div
              key={e.id}
              className={`group relative isolate flex min-h-[4.25rem] items-stretch gap-1 rounded-xl border transition-colors ${
                activeId === e.id
                  ? "border-border/80 bg-surface"
                  : "border-transparent hover:bg-surface"
              }`}
            >
              {isEditing ? (
                <div className="flex min-w-0 flex-1 items-center px-2 py-1.5">
                  <input
                    ref={renameInputRef}
                    value={renameDraft}
                    onChange={(ev) => onRenameDraft(ev.target.value)}
                    onFocus={(ev) => {
                      onRenameFocus(true);
                      ev.target.select();
                    }}
                    onBlur={() => {
                      onRenameFocus(false);
                      onCommitRename();
                    }}
                    className={`min-w-0 flex-1 rounded-md text-[13px] font-medium leading-snug outline-none transition-[background-color,border-color,box-shadow,padding] ${
                      renameFieldFocused
                        ? "border border-border bg-surface px-2 py-1 shadow-sm"
                        : "border border-transparent bg-transparent px-1 py-0.5"
                    }`}
                    onKeyDown={(ev) => {
                      if (ev.key === "Enter") {
                        ev.preventDefault();
                        onCommitRename();
                      }
                      if (ev.key === "Escape") {
                        ev.preventDefault();
                        onCancelRename();
                      }
                    }}
                  />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => onSelectEntry(e.id)}
                  className="hover:bg-default/25 flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg px-2.5 pb-2 pt-2.5 text-left text-sm transition-colors"
                >
                  <div className="min-h-[2.75rem] shrink-0">
                    <div className="line-clamp-2 text-[13px] font-medium leading-snug">
                      {rowLabel}
                    </div>
                  </div>
                  <div className="border-border/50 text-muted mt-auto shrink-0 space-y-0.5 border-t pt-2 text-[11px] tabular-nums">
                    <div className="break-words leading-relaxed">
                      {formatChatTime(e.createdAt)}
                    </div>
                    {e.maxRows != null && (
                      <div className="text-muted/85">LIMIT {e.maxRows}</div>
                    )}
                  </div>
                </button>
              )}
              {!isEditing && (
                <Dropdown.Root>
                  <Dropdown.Trigger
                    aria-label={t("home.analytics.chatRowMenuAria")}
                    className="mr-0.5 my-auto inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted opacity-70 transition-opacity hover:bg-default hover:opacity-100 group-hover:opacity-100"
                  >
                    <Icon icon="mdi:dots-vertical" width={16} />
                  </Dropdown.Trigger>
                  <Dropdown.Popover placement="bottom end">
                    <Dropdown.Menu>
                      <Dropdown.Item
                        textValue={t("home.analytics.renameChat")}
                        onAction={() => onStartEditingRow(e)}
                      >
                        <span className="flex items-center gap-2">
                          <Icon icon="mdi:pencil-outline" width={18} />
                          {t("home.analytics.renameChat")}
                        </span>
                      </Dropdown.Item>
                      <Dropdown.Item
                        textValue={t("home.analytics.deleteChat")}
                        onAction={() => void onConfirmDeleteOne(e.id)}
                      >
                        <span className="flex items-center gap-2 text-danger">
                          <Icon icon="mdi:delete-outline" width={18} />
                          {t("home.analytics.deleteChat")}
                        </span>
                      </Dropdown.Item>
                    </Dropdown.Menu>
                  </Dropdown.Popover>
                </Dropdown.Root>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
