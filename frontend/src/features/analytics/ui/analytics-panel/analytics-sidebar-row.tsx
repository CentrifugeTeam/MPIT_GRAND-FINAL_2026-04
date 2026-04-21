import type { RefObject } from "react";
import { Dropdown } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { AnalyticsChatEntry } from "@/features/analytics/model/analytics-chat-store";
import { formatChatTime } from "@/features/analytics/lib/format-chat-time";

export type AnalyticsSidebarRowProps = {
  entry: AnalyticsChatEntry;
  rowLabel: string;
  activeId: string | null;
  editingRowId: string | null;
  renameDraft: string;
  renameFieldFocused: boolean;
  renameInputRef: RefObject<HTMLInputElement | null>;
  onRenameDraft: (v: string) => void;
  onRenameFocus: (focused: boolean) => void;
  onCommitRename: () => void;
  onCancelRename: () => void;
  onSelectEntry: (id: string) => void;
  onStartEditingRow: (e: AnalyticsChatEntry) => void;
  onDeleteHistoryEntry: (rowId: string) => void;
  t: (key: string) => string;
};

export function AnalyticsSidebarRow({
  entry: e,
  rowLabel,
  activeId,
  editingRowId,
  renameDraft,
  renameFieldFocused,
  renameInputRef,
  onRenameDraft,
  onRenameFocus,
  onCommitRename,
  onCancelRename,
  onSelectEntry,
  onStartEditingRow,
  onDeleteHistoryEntry,
  t,
}: AnalyticsSidebarRowProps) {
  const isEditing = editingRowId === e.id;
  return (
    <div
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
            <div className="line-clamp-2 text-[13px] font-medium leading-snug">{rowLabel}</div>
          </div>
          <div className="border-border/50 text-muted mt-auto shrink-0 space-y-0.5 border-t pt-2 text-[11px] tabular-nums">
            <div className="break-words leading-relaxed">{formatChatTime(e.createdAt)}</div>
            {e.kind === "sql_job" && e.maxRows != null && (
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
                onAction={() => void onDeleteHistoryEntry(e.id)}
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
}
