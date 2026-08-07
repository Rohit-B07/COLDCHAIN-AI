"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { PredictionHistoryPage } from "@/lib/types";

/**
 * Fetches the paginated prediction-history feed for the dashboard table.
 *
 * The history endpoint returns the newest predictions first, so the first
 * page is the most recent activity.
 */

const HISTORY_SIZE = 10;

export function usePredictionHistory() {
  return useQuery({
    queryKey: ["dashboard", "prediction-history", HISTORY_SIZE],
    queryFn: () =>
      apiClient.get<PredictionHistoryPage>(
        `/predictions/history?page=1&size=${HISTORY_SIZE}`,
      ),
  });
}
