import { useEffect, useState } from "react";
import { AnimatePresence } from "motion/react";
import { Icon } from "@iconify/react";

import type { AnalyticsSidebarProps } from "../analytics-panel/analytics-sidebar";
import {
  FIGMA_SIDEBAR_COLLAPSED_PX,
  FIGMA_SIDEBAR_EXPANDED_PX,
} from "./figma-tokens";
import { FigmaConfirmDialog } from "./figma-confirm-dialog";
import { FigmaSearchModal } from "./figma-search-modal";
import { FigmaSimpleTooltip } from "./figma-simple-tooltip";
import { FigmaSidebarHistorySection } from "./figma-sidebar-history-section";
import { FigmaSidebarPrimaryNav } from "./figma-sidebar-primary-nav";

export type FigmaAnalyticsSidebarProps = AnalyticsSidebarProps & {
  isOpen: boolean;
  onToggle: () => void;
};

export function FigmaAnalyticsSidebar({
  isOpen,
  onToggle,
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
}: FigmaAnalyticsSidebarProps) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [deleteAllOpen, setDeleteAllOpen] = useState(false);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const sidebarWidth = isOpen ? FIGMA_SIDEBAR_EXPANDED_PX : FIGMA_SIDEBAR_COLLAPSED_PX;

  return (
    <>
      <div
        className="relative flex h-full min-h-0 shrink-0 flex-col transition-all duration-300"
        style={{ width: sidebarWidth }}
      >
        <div className="flex h-full min-h-0 w-full flex-col overflow-hidden rounded-br-[16px] rounded-tr-[16px] bg-[#060607]">
          <div className="flex h-full min-h-0 flex-col gap-[20px] px-[8px] py-[16px]">
            <div className="flex w-full shrink-0 flex-col gap-[20px]">
              <div
                className="flex w-full items-center"
                style={{
                  justifyContent: isOpen ? "space-between" : "center",
                  paddingLeft: isOpen ? 8 : 0,
                }}
              >
                <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#3f3f46] to-[#18181b]">
                  <Icon icon="mdi:account" className="text-[#fcfcfc]" width={18} />
                </div>
                {isOpen && (
                  <button
                    type="button"
                    onClick={onToggle}
                    className="flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-[24px] transition-all duration-200 hover:bg-[#27272a]/60 active:scale-[0.97]"
                    title={t("home.figma.openSidebar")}
                  >
                    <Icon icon="mdi:chevron-double-left" className="text-[#fcfcfc]" width={20} />
                  </button>
                )}
              </div>

              <FigmaSidebarPrimaryNav
                isOpen={isOpen}
                onOpenSearch={() => setSearchOpen(true)}
                onStartNewChat={onStartNewChat}
                t={t}
              />
            </div>

            {isOpen && (
              <FigmaSidebarHistorySection
                historyOpen={historyOpen}
                onToggleHistory={() => setHistoryOpen(!historyOpen)}
                entries={entries}
                titles={titles}
                activeId={activeId}
                editingRowId={editingRowId}
                renameDraft={renameDraft}
                renameFieldFocused={renameFieldFocused}
                renameInputRef={renameInputRef}
                historyBusy={historyBusy}
                onRenameDraft={onRenameDraft}
                onRenameFocus={onRenameFocus}
                onCommitRename={onCommitRename}
                onCancelRename={onCancelRename}
                onSelectEntry={onSelectEntry}
                onStartNewChat={onStartNewChat}
                onLoadHistory={onLoadHistory}
                onRequestDeleteAll={() => setDeleteAllOpen(true)}
                onStartEditingRow={onStartEditingRow}
                onRequestDeleteRow={(id) => setPendingDeleteId(id)}
                t={t}
              />
            )}

            <div
              className="mt-auto flex w-full shrink-0 items-center pt-2"
              style={{
                justifyContent: isOpen ? "flex-start" : "center",
                padding: isOpen ? "0 8px" : "0",
              }}
            >
              {!isOpen && (
                <FigmaSimpleTooltip label={t("home.figma.openSidebar")} side="right">
                  <button
                    type="button"
                    onClick={onToggle}
                    className="flex size-8 cursor-pointer items-center justify-center rounded-[24px] transition-all hover:bg-[#27272a]/60 active:scale-[0.97]"
                  >
                    <Icon icon="mdi:chevron-double-right" className="text-[#fcfcfc]" width={20} />
                  </button>
                </FigmaSimpleTooltip>
              )}
            </div>
          </div>
        </div>
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 rounded-br-[16px] rounded-tr-[16px] border border-b border-r border-t border-[#28282c] border-solid"
        />
      </div>

      <AnimatePresence>
        {pendingDeleteId && (
          <FigmaConfirmDialog
            open
            title={t("home.analytics.deleteChatTitle")}
            message={t("home.analytics.deleteChatBody")}
            confirmLabel={t("home.analytics.deleteChatConfirm")}
            cancelLabel={t("home.analytics.deleteChatCancel")}
            danger
            onConfirm={() => {
              void onDeleteHistoryEntry(pendingDeleteId);
              setPendingDeleteId(null);
            }}
            onCancel={() => setPendingDeleteId(null)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {deleteAllOpen && (
          <FigmaConfirmDialog
            open
            title={t("home.analytics.deleteAllHistory")}
            message={t("home.analytics.deleteAllHistoryDetail")}
            confirmLabel={t("home.analytics.deleteChatConfirm")}
            cancelLabel={t("home.analytics.deleteChatCancel")}
            danger
            onConfirm={() => {
              void onClearAllHistory();
              setDeleteAllOpen(false);
            }}
            onCancel={() => setDeleteAllOpen(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {searchOpen && (
          <FigmaSearchModal
            t={t}
            entries={entries}
            titles={titles}
            activeId={activeId}
            onClose={() => setSearchOpen(false)}
            onSelectEntry={onSelectEntry}
            onStartNewChat={onStartNewChat}
          />
        )}
      </AnimatePresence>
    </>
  );
}
