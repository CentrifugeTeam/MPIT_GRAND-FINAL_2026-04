import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router";

import {
  AnalyticsResults,
  FigmaAnalyticsMain,
  FigmaAnalyticsSidebar,
  useAnalyticsPanel,
} from "@/features/analytics";

export function AnalyticsWorkspace() {
  const p = useAnalyticsPanel();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [params, setParams] = useSearchParams();

  const { entries, historyBusy, selectEntry } = p;

  useEffect(() => {
    if (historyBusy) return;
    const cid = params.get("analyticsChat")?.trim();
    if (!cid) return;
    if (entries.some((e) => e.id === cid)) {
      selectEntry(cid);
    }
    setParams(
      (prev) => {
        const n = new URLSearchParams(prev);
        n.delete("analyticsChat");
        return n;
      },
      { replace: true },
    );
  }, [entries, historyBusy, selectEntry, params, setParams]);

  const handleShareChat = useCallback(async () => {
    if (!p.nlConversationId) return;
    const u = new URL(window.location.href);
    u.searchParams.set("analyticsChat", p.nlConversationId);
    try {
      await navigator.clipboard.writeText(u.toString());
    } catch {
      /* ignore */
    }
  }, [p.nlConversationId]);

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
          onSelectEntry={p.selectEntry}
          onStartNewChat={() => void p.startNewChat()}
          onLoadHistory={() => void p.loadHistory()}
          onClearAllHistory={() => void p.clearAllHistoryEntries()}
          onStartEditingRow={p.startEditingRow}
          onDeleteHistoryEntry={(id) => void p.deleteHistoryEntry(id)}
          t={p.t}
        />
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <FigmaAnalyticsMain
            t={p.t}
            sidebarOpen={sidebarOpen}
            onOpenSidebar={() => setSidebarOpen(true)}
            interpretationHint={p.interpretationHint}
            hideInterpretationStrip={!!p.result}
            question={p.question}
            composerBusy={p.composerBusy}
            nlChatLines={p.nlChatLines}
            nlChatReady={p.nlChatReady}
            dataSources={p.dataSources}
            selectedSourceKey={p.selectedSourceKey}
            selectedSourceLabel={p.selectedSourceLabel}
            onSourceKeyChange={p.setSelectedSourceKey}
            dataSourcesLoaded={p.dataSourcesLoaded}
            nlConversationId={p.nlConversationId}
            onShareChat={handleShareChat}
            historyBusy={p.historyBusy}
            onRefreshHistory={() => void p.loadHistory()}
            onQuestionChange={p.setQuestion}
            onSend={() => void p.sendComposerMessage()}
            onStartNewChat={() => void p.startNewChat()}
          />

          {p.result && (
            <div className="shrink-0 border-t border-border">
              <div className="max-h-[min(45vh,520px)] w-full overflow-y-auto px-5 py-4">
                <AnalyticsResults
                  t={p.t}
                  result={p.result}
                  showChart={p.showChart}
                  chartPayload={p.chartPayload}
                  interpretationFallback={p.interpretationHint}
                />
              </div>
            </div>
          )}
        </div>
    </div>
  );
}

