import { useQuery } from '@tanstack/react-query';
import { fetchAnalyticsDataSources } from '@/features/analytics/api/analytics-api';

export function useDataSources() {
  return useQuery({
    queryKey: ['data-sources'],
    queryFn: () => fetchAnalyticsDataSources(),
  });
}
