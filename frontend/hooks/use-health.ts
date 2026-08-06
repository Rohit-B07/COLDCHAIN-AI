"use client";

import { useCallback, useEffect, useState } from "react";

import { apiClient, ApiError } from "@/lib/api/client";

interface UseHealthResult {
  healthy: boolean | null;
  database: string | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/** Poll the backend health endpoint so the UI reflects service status. */
export function useHealth(intervalMs = 30_000): UseHealthResult {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [database, setDatabase] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiClient.get<{ status: string; database: string }>(
        "/health",
      );
      setHealthy(result.status === "ok");
      setDatabase(result.database);
      setError(null);
    } catch (err) {
      setHealthy(false);
      setError(err instanceof ApiError ? err.message : "Unable to reach API");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    if (intervalMs <= 0) return;
    const timer = setInterval(() => void refresh(), intervalMs);
    return () => clearInterval(timer);
  }, [refresh, intervalMs]);

  return { healthy, database, loading, error, refresh };
}
