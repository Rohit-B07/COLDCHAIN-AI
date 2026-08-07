"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { NotificationFeed } from "@/lib/types";

/**
 * Fetches the aggregated notification feed for the dashboard's Notification
 * Center. Defaults to the latest five notifications, newest first.
 */
export function useNotifications(size = 5) {
  return useQuery({
    queryKey: ["dashboard", "notifications", size],
    queryFn: () =>
      apiClient.get<NotificationFeed>(`/notifications?page=1&size=${size}`),
  });
}
