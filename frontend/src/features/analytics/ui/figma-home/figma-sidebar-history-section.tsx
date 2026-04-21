import type { RefObject } from "react";
import { Dropdown } from "@heroui/react";
import { Icon } from "@iconify/react";

import type { AnalyticsChatEntry } from "../../model/analytics-chat-store";
import {
  FIGMA_DROPDOWN_ITEM,
  FIGMA_DROPDOWN_ITEM_DANGER,
  FIGMA_DROPDOWN_MENU,
  FIGMA_DROPDOWN_POPOVER,
} from "./figma-heroui-dropdown-classes";
import { FigmaSidebarHistoryRows } from "./figma-sidebar-history-rows";

export type FigmaSidebarHistorySectionProps = {
  historyOpen: boolean;
  onToggleHistory: () => void;
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
  onRequestDeleteAll: () => void;
  onStartEditingRow: (e: AnalyticsChatEntry) => void;
  onRequestDeleteRow: (id: string) => void;
  t: (key: string) => string;
};

export function FigmaSidebarHistorySection({
  historyOpen,
  onToggleHistory,
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
  onRequestDeleteAll,
  onStartEditingRow,
  onRequestDeleteRow,
  t,
}: FigmaSidebarHistorySectionProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-[8px] pt-1 pb-[16px]">
      <div className="flex shrink-0 items-center gap-[4px] pl-[12px]">
        <button
          type="button"
          onClick={onToggleHistory}
          className="flex cursor-pointer items-center gap-[4px] font-sans text-[14px] font-medium leading-[16px] tracking-[-0.14px] text-[#fcfcfc] transition-opacity duration-150 hover:opacity-70"
        >
          {t("home.figma.history")}
          <Icon
            icon="mdi:chevron-down"
            width={16}
            className={`text-[#fcfcfc] transition-transform ${historyOpen ? "" : "-rotate-90"}`}
          />
        </button>
        <div className="ml-auto">
          <Dropdown.Root>
            <Dropdown.Trigger
              aria-label={t("home.analytics.sidebarMenuAria")}
              className="inline-flex size-8 shrink-0 items-center justify-center rounded-lg text-[#a1a1aa] hover:bg-[#27272a] hover:text-[#fcfcfc]"
            >
              <Icon icon="mdi:dots-vertical" width={18} />
            </Dropdown.Trigger>
            <Dropdown.Popover placement="bottom end" className={FIGMA_DROPDOWN_POPOVER}>
              <Dropdown.Menu className={FIGMA_DROPDOWN_MENU}>
                <Dropdown.Item
                  className={FIGMA_DROPDOWN_ITEM}
                  textValue={t("home.analytics.newQuestion")}
                  onAction={onStartNewChat}
                >
                  <span className="flex items-center gap-2">
                    <Icon icon="mdi:message-plus-outline" width={18} />
                    {t("home.analytics.newQuestion")}
                  </span>
                </Dropdown.Item>
                <Dropdown.Item
                  className={FIGMA_DROPDOWN_ITEM}
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
                  className={FIGMA_DROPDOWN_ITEM_DANGER}
                  textValue={t("home.analytics.deleteAllHistory")}
                  onAction={() => {
                    if (entries.length > 0) onRequestDeleteAll();
                  }}
                >
                  <span className="flex items-center gap-2">
                    <Icon icon="mdi:delete-sweep-outline" width={18} />
                    {t("home.analytics.deleteAllHistory")}
                  </span>
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown.Popover>
          </Dropdown.Root>
        </div>
      </div>

      {historyOpen && (
        <div className="flex min-h-0 flex-1 flex-col gap-[4px] overflow-y-auto">
          {entries.length === 0 && (
            <p className="px-[12px] py-3 font-sans text-xs text-[#71717a]">
              {t("home.analytics.sidebarEmpty")}
            </p>
          )}
          <FigmaSidebarHistoryRows
            entries={entries}
            titles={titles}
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
            onRequestDeleteRow={onRequestDeleteRow}
            t={t}
          />
        </div>
      )}
    </div>
  );
}
