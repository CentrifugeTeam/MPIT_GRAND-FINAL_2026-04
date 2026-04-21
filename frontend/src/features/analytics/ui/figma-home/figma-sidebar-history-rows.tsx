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

export type FigmaSidebarHistoryRowsProps = {
  entries: AnalyticsChatEntry[];
  titles: Record<string, string>;
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
  onRequestDeleteRow: (id: string) => void;
  t: (key: string) => string;
};

export function FigmaSidebarHistoryRows({
  entries,
  titles,
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
  onRequestDeleteRow,
  t,
}: FigmaSidebarHistoryRowsProps) {
  return (
    <>
      {entries.map((e) => {
    const rowLabel = titles[e.id] ?? e.question;
    const isEditing = editingRowId === e.id;
    return (
      <div
        key={e.id}
        className={`group relative w-full shrink-0 cursor-pointer rounded-[12px] transition-colors duration-150 ${
          activeId === e.id ? "bg-[#27272a]" : "hover:bg-[#27272a]/60"
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
              className={`min-w-0 flex-1 rounded-md font-sans text-[13px] font-medium leading-snug text-[#fcfcfc] outline-none transition-[background-color,border-color,padding] ${
                renameFieldFocused
                  ? "border border-[#28282c] bg-[#18181b] px-2 py-1"
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
          <>
            <div className="flex min-h-[36px] w-full items-center gap-2 px-[12px] py-[6px]">
              <button
                type="button"
                onClick={() => onSelectEntry(e.id)}
                className="min-w-0 flex-1 truncate text-left font-sans text-[14px] font-medium leading-snug text-[#fcfcfc]"
              >
                {rowLabel}
              </button>
              <Dropdown.Root>
                <Dropdown.Trigger
                  aria-label={t("home.analytics.chatRowMenuAria")}
                  className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-[#fcfcfc] opacity-70 transition-opacity hover:bg-[#323236] hover:opacity-100 group-hover:opacity-100"
                >
                  <Icon icon="mdi:dots-vertical" width={16} />
                </Dropdown.Trigger>
                <Dropdown.Popover placement="bottom end" className={FIGMA_DROPDOWN_POPOVER}>
                  <Dropdown.Menu className={FIGMA_DROPDOWN_MENU}>
                    <Dropdown.Item
                      className={FIGMA_DROPDOWN_ITEM}
                      textValue={t("home.analytics.renameChat")}
                      onAction={() => onStartEditingRow(e)}
                    >
                      <span className="flex items-center gap-2">
                        <Icon icon="mdi:pencil-outline" width={18} />
                        {t("home.analytics.renameChat")}
                      </span>
                    </Dropdown.Item>
                    <Dropdown.Item
                      className={FIGMA_DROPDOWN_ITEM_DANGER}
                      textValue={t("home.analytics.deleteChat")}
                      onAction={() => onRequestDeleteRow(e.id)}
                    >
                      <span className="flex items-center gap-2">
                        <Icon icon="mdi:delete-outline" width={18} />
                        {t("home.analytics.deleteChat")}
                      </span>
                    </Dropdown.Item>
                  </Dropdown.Menu>
                </Dropdown.Popover>
              </Dropdown.Root>
            </div>
          </>
        )}
      </div>
    );
      })}
    </>
  );
}
