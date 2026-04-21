import type { RefObject } from "react";
import { Dropdown } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";

import { AnalyticsSidebarRow } from "./analytics-sidebar-row";

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
  onClearAllHistory: () => void;
  onStartEditingRow: (e: AnalyticsChatEntry) => void;
  onDeleteHistoryEntry: (rowId: string) => void;
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
  onClearAllHistory,
  onStartEditingRow,
  onDeleteHistoryEntry,
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
                  if (entries.length > 0) void onClearAllHistory();
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
        {entries.map((e) => (
          <AnalyticsSidebarRow
            key={e.id}
            entry={e}
            rowLabel={titles[e.id] ?? e.question}
            activeId={activeId}
            editingRowId={editingRowId}
            renameDraft={renameDraft}
            renameFieldFocused={renameFieldFocused}
            renameInputRef={renameInputRef}
            onRenameDraft={onRenameDraft}
            onRenameFocus={onRenameFocus}
            onCommitRename={onCommitRename}
            onCancelRename={onCancelRename}
            onSelectEntry={onSelectEntry}
            onStartEditingRow={onStartEditingRow}
            onDeleteHistoryEntry={onDeleteHistoryEntry}
            t={t}
          />
        ))}
      </div>
    </aside>
  );
}
