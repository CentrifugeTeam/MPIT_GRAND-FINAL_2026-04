import { useQuery } from '@tanstack/react-query';
import { fetchReportTaskTemplates } from '@/features/analytics/api/analytics-api';

export function useReportTemplates() {
  return useQuery({
    queryKey: ['report-task-templates'],
    queryFn: () => fetchReportTaskTemplates(100, 0),
  });
}
