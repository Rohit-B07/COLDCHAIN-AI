"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { AnalyticsDashboardResponse } from "@/lib/types";

/**
 * Fetches the aggregated operational KPIs for the dashboard's Analytics
 * Summary section.
 */
export function useAnalytics() {
  return useQuery({
    queryKey: ["dashboard", "analytics"],
    queryFn: () =>
      apiClient.get<AnalyticsDashboardResponse>("/analytics/dashboard"),
  });
}
