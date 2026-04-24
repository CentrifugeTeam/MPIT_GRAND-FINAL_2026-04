import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchChatInvites } from "../api/analytics-api";
import { chatInviteToViewerEntry } from "../lib/history-mapper";
import { dedupeAnalyticsChatEntriesById } from "./analytics-chat-store";

export const CHAT_INVITES_QUERY_KEY = ["analytics", "chat-invites"] as const;

export function useAcceptedChatInvites() {
  const query = useQuery({
    queryKey: CHAT_INVITES_QUERY_KEY,
    queryFn: fetchChatInvites,
  });

  const acceptedEntries = useMemo(() => {
    const items = query.data ?? [];
    const mapped = items
      .filter((i) => i.status === "accepted")
      .map(chatInviteToViewerEntry);
    return dedupeAnalyticsChatEntriesById(mapped);
  }, [query.data]);

  return { ...query, acceptedEntries };
}
