import { useQuery } from '@tanstack/react-query';

import { fetchChatSuggestions } from '../api/analytics-api';

export function useChatSuggestions(sourceKey: string | null) {
  return useQuery({
    queryKey: ['analytics-chat-suggestions', sourceKey ?? null],
    queryFn: () => fetchChatSuggestions(sourceKey, 'ru'),
    staleTime: 30_000,
  });
}
