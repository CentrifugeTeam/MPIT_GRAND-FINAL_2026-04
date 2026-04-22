import { useQuery } from "@tanstack/react-query";
import { fetchReportTasks } from "@/features/analytics/api/analytics-api";

export function useReportTasks() {
  return useQuery({
    queryKey: ["report-tasks"],
    queryFn: () => fetchReportTasks(),
  });
}

