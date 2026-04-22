import { useState } from "react";
import { Button } from "@heroui/react";
import { Icon } from "@iconify/react";
import { useNavigate } from "react-router";

import { FigmaAnalyticsSidebar, useAnalyticsPanel } from "@/features/analytics";

export function ReportsDashboard() {
  const p = useAnalyticsPanel();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex min-h-0 w-full flex-1 items-stretch gap-4 overflow-hidden bg-background py-4 pl-0 pr-4">
      <div className="flex min-h-0 shrink-0 self-stretch">
        <FigmaAnalyticsSidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
          entries={p.entries}
          titles={p.titles}
          activeId={p.activeId}
          editingRowId={p.editingRowId}
          renameDraft={p.renameDraft}
          renameFieldFocused={p.renameFieldFocused}
          renameInputRef={p.renameInputRef}
          historyBusy={p.historyBusy}
          onRenameDraft={p.setRenameDraft}
          onRenameFocus={p.setRenameFieldFocused}
          onCommitRename={p.commitRename}
          onCancelRename={p.cancelRename}
          onSelectEntry={(entryId) => {
            const entry = p.entries.find((e) => e.id === entryId);
            const chatId = entry?.conversationId;
            if (!chatId) return;
            void navigate(`/home/${chatId}`);
          }}
          onStartNewChat={() => void navigate("/home")}
          onLoadHistory={() => void p.loadHistory()}
          onClearAllHistory={() => void p.clearAllHistoryEntries()}
          onStartEditingRow={p.startEditingRow}
          onDeleteHistoryEntry={(id) => void p.deleteHistoryEntry(id)}
          t={p.t}
        />
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <section className="flex min-h-0 flex-1 flex-col overflow-y-auto rounded-2xl border border-border bg-background p-5">
          <div className="flex items-center justify-between gap-4">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="flex size-8 shrink-0 cursor-pointer items-center justify-center rounded-[12px] transition-all hover:bg-content2 active:scale-[0.97]"
                aria-label={p.t("home.figma.openSidebar")}
              >
                <Icon icon="mdi:menu" width={18} className="text-foreground" />
              </button>
            )}
            <h1 className="text-2xl font-semibold text-foreground">
              {p.t("reports.title")}
            </h1>
            <Button variant="outline">
              <Icon icon="mdi:plus" width={16} className="mr-1" />
              {p.t("reports.createTask")}
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}

