"use client";

import {
  AlertTriangle,
  Bell,
  PackageSearch,
  Sparkles,
  Thermometer,
  Truck,
} from "lucide-react";

import { StatCard } from "@/components/dashboard/stat-card";
import type { AnalyticsDashboardResponse } from "@/lib/types";

interface AnalyticsSummaryProps {
  data?: AnalyticsDashboardResponse;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
}

/**
 * Operational insight KPI cards derived from the analytics endpoint.
 */
export function AnalyticsSummary({
  data,
  isLoading,
  isError,
  onRetry,
}: AnalyticsSummaryProps) {
  const shipments = data?.shipments;
  const predictions = data?.predictions;
  const alerts = data?.alerts;
  const notifications = data?.notifications;
  const temperature = data?.temperature;

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <StatCard
        title="Total Shipments"
        icon={PackageSearch}
        value={shipments?.total}
        detail={`${shipments?.active ?? 0} active`}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
      <StatCard
        title="Active Shipments"
        icon={Truck}
        value={shipments?.active}
        detail={`${shipments?.delayed ?? 0} delayed`}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
      <StatCard
        title="Critical Predictions"
        icon={Sparkles}
        value={predictions?.critical}
        detail={`${predictions?.high ?? 0} high risk`}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
      <StatCard
        title="Open Alerts"
        icon={AlertTriangle}
        value={alerts?.open}
        detail={`${alerts?.resolved ?? 0} resolved`}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
      <StatCard
        title="Unread Notifications"
        icon={Bell}
        value={notifications?.unread}
        detail={`${notifications?.total ?? 0} total`}
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
      <StatCard
        title="Average Temperature"
        icon={Thermometer}
        value={temperature ? Math.round(temperature.average) : undefined}
        detail={
          temperature
            ? `min ${temperature.minimum}°C · max ${temperature.maximum}°C`
            : undefined
        }
        isLoading={isLoading}
        isError={isError}
        onRetry={onRetry}
      />
    </div>
  );
}
