import { useCallback, useEffect, useState } from 'react';

import { fetchChatInvites } from '@/features/analytics/api/analytics-api';

export function usePendingChatInvites() {
  const [invites, setInvites] = useState<ChatInviteItem[]>([]);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    setBusy(true);
    try {
      const rows = await fetchChatInvites();
      setInvites(rows);
    } catch {
      setInvites([]);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { invites, busy, reload };
}
