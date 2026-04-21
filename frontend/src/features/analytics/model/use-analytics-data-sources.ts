import { useEffect, useMemo, useState } from "react";

import {
  fetchAnalyticsDataSources,
  type AnalyticsDataSourceItem,
} from "../api/analytics-api";

export function useAnalyticsDataSources() {
  const [dataSources, setDataSources] = useState<AnalyticsDataSourceItem[]>([]);
  const [selectedSourceKey, setSelectedSourceKey] = useState<string | null>(null);
  const [dataSourcesLoaded, setDataSourcesLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchAnalyticsDataSources()
      .then((d) => {
        if (cancelled) return;
        setDataSources(d.items);
        const k =
          d.default_key ??
          d.items.find((x) => x.is_default)?.key ??
          d.items[0]?.key ??
          null;
        setSelectedSourceKey(k);
      })
      .catch(() => {
        if (!cancelled) {
          setDataSources([]);
          setDefaultSourceKey(null);
          setSelectedSourceKey(null);
        }
      })
      .finally(() => {
        if (!cancelled) setDataSourcesLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedSourceLabel = useMemo(() => {
    if (!selectedSourceKey) return "";
    const s = dataSources.find((x) => x.key === selectedSourceKey);
    return s?.display_name ?? "";
  }, [dataSources, selectedSourceKey]);

  const nlChatReady = useMemo(
    () =>
      dataSourcesLoaded && (dataSources.length === 0 || selectedSourceKey != null),
    [dataSources.length, dataSourcesLoaded, selectedSourceKey],
  );

  return {
    dataSources,
    selectedSourceKey,
    setSelectedSourceKey,
    dataSourcesLoaded,
    selectedSourceLabel,
    nlChatReady,
  };
}
