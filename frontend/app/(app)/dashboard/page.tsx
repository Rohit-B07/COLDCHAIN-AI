"use client";

import { useMemo } from "react";
import {
  Bell,
  Boxes,
  Map,
  PackageSearch,
  Sparkles,
  Truck,
  Users,
  Warehouse,
} from "lucide-react";

import { AlertSeverityChart } from "@/components/dashboard/alert-severity-chart";
import { ChartCard } from "@/components/dashboard/chart-card";
import { ShipmentStatusChart } from "@/components/dashboard/shipment-status-chart";
import { StatCard } from "@/components/dashboard/stat-card";
import { TemperatureTrendChart } from "@/components/dashboard/temperature-trend-chart";
import { VehicleUtilizationChart } from "@/components/dashboard/vehicle-utilization-chart";
import {
  useAlerts,
  useDrivers,
  usePhcs,
  usePredictions,
  useRoutes,
  useShipments,
  useVehicles,
  useWarehouses,
} from "@/hooks/use-dashboard";
import type { AlertRead, PredictionRead, ShipmentRead, VehicleRead } from "@/lib/types";

const ACTIVE_ROUTE_STATUSES = ["planned", "optimized", "selected"];
const ACTIVE_ALERT_STATUSES = ["open", "acknowledged"];

function groupBy<T>(items: T[], key: (item: T) => string) {
  return items.reduce<Record<string, number>>((acc, item) => {
    const k = key(item);
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});
}

function shipmentStatusData(shipments: ShipmentRead[]) {
  const counts = groupBy(shipments, (s) => s.status);
  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

function alertSeverityData(alerts: AlertRead[]) {
  const open = alerts.filter((a) => ACTIVE_ALERT_STATUSES.includes(a.status));
  const counts = groupBy(open, (a) => a.severity);
  const order = ["critical", "warning", "info"];
  return order
    .filter((name) => counts[name] !== undefined)
    .map((name) => ({ name, value: counts[name] as number }));
}

function vehicleUtilizationData(vehicles: VehicleRead[]) {
  const counts = groupBy(vehicles, (v) => v.status);
  const order = ["active", "maintenance", "retired"];
  return order
    .filter((name) => counts[name] !== undefined)
    .map((name) => ({ name, value: counts[name] as number }));
}

function temperatureTrendData(predictions: PredictionRead[]) {
  return predictions
    .filter((p) => p.created_at)
    .slice()
    .sort(
      (a, b) =>
        new Date(a.created_at ?? 0).getTime() -
        new Date(b.created_at ?? 0).getTime(),
    )
    .slice(-20)
    .map((p) => ({
      label: new Date(p.created_at ?? 0).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
      min: p.expected_min_temp,
      max: p.expected_max_temp,
    }));
}

export default function DashboardPage() {
  const shipments = useShipments();
  const routes = useRoutes();
  const warehouses = useWarehouses();
  const phcs = usePhcs();
  const vehicles = useVehicles();
  const drivers = useDrivers();
  const alerts = useAlerts();
  const predictions = usePredictions();

  const shipmentItems = useMemo(() => shipments.data?.items ?? [], [shipments.data]);
  const activeRouteCount = useMemo(
    () =>
      (routes.data?.items ?? []).filter((r) =>
        ACTIVE_ROUTE_STATUSES.includes(r.status),
      ).length,
    [routes.data],
  );
  const vehicleItems = useMemo(() => vehicles.data?.items ?? [], [vehicles.data]);
  const alertItems = useMemo(() => alerts.data?.items ?? [], [alerts.data]);
  const predictionItems = useMemo(
    () => predictions.data?.items ?? [],
    [predictions.data],
  );

  const totalOpenAlerts = useMemo(
    () => alertItems.filter((a) => ACTIVE_ALERT_STATUSES.includes(a.status)).length,
    [alertItems],
  );
  const criticalAlerts = useMemo(
    () => alertItems.filter((a) => a.severity === "critical" && ACTIVE_ALERT_STATUSES.includes(a.status)).length,
    [alertItems],
  );
  const avgRisk = useMemo(() => {
    if (predictionItems.length === 0) return 0;
    const sum = predictionItems.reduce((acc, p) => acc + p.excursion_risk, 0);
    return Math.round((sum / predictionItems.length) * 100);
  }, [predictionItems]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Cold-chain operations at a glance
        </p>
      </div>

      <section aria-label="Summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Shipments"
          icon={PackageSearch}
          value={shipments.data?.total ?? shipmentItems.length}
          detail={`${shipmentItems.filter((s) => s.status === "in_transit").length} in transit`}
          isLoading={shipments.isLoading}
          isError={shipments.isError}
          onRetry={() => void shipments.refetch()}
        />
        <StatCard
          title="Active Routes"
          icon={Map}
          value={activeRouteCount}
          detail="Planned, optimised or selected"
          isLoading={routes.isLoading}
          isError={routes.isError}
          onRetry={() => void routes.refetch()}
        />
        <StatCard
          title="Warehouses"
          icon={Warehouse}
          value={warehouses.data?.total ?? 0}
          detail={`${warehouses.data?.pages ?? 0} pages of records`}
          isLoading={warehouses.isLoading}
          isError={warehouses.isError}
          onRetry={() => void warehouses.refetch()}
        />
        <StatCard
          title="Health Centres"
          icon={Boxes}
          value={phcs.data?.total ?? 0}
          detail="PHC delivery destinations"
          isLoading={phcs.isLoading}
          isError={phcs.isError}
          onRetry={() => void phcs.refetch()}
        />
        <StatCard
          title="Vehicles"
          icon={Truck}
          value={vehicles.data?.total ?? 0}
          detail={`${vehicleItems.filter((v) => v.status === "active").length} active`}
          isLoading={vehicles.isLoading}
          isError={vehicles.isError}
          onRetry={() => void vehicles.refetch()}
        />
        <StatCard
          title="Drivers"
          icon={Users}
          value={drivers.data?.total ?? 0}
          detail={`${(drivers.data?.items ?? []).filter((d) => d.status === "available").length} available`}
          isLoading={drivers.isLoading}
          isError={drivers.isError}
          onRetry={() => void drivers.refetch()}
        />
        <StatCard
          title="Open Alerts"
          icon={Bell}
          value={totalOpenAlerts}
          detail={`${criticalAlerts} critical`}
          isLoading={alerts.isLoading}
          isError={alerts.isError}
          onRetry={() => void alerts.refetch()}
        />
        <StatCard
          title="Predictions"
          icon={Sparkles}
          value={predictions.data?.total ?? 0}
          detail={`Avg excursion risk ${avgRisk}%`}
          isLoading={predictions.isLoading}
          isError={predictions.isError}
          onRetry={() => void predictions.refetch()}
        />
      </section>

      <section aria-label="Analytics" className="grid gap-4 lg:grid-cols-2">
        <ChartCard
          title="Shipment Status"
          description="Current distribution by status"
          isLoading={shipments.isLoading}
          isError={shipments.isError}
          isEmpty={shipmentItems.length === 0}
          onRetry={() => void shipments.refetch()}
          emptyMessage="No shipments recorded"
        >
          <ShipmentStatusChart data={shipmentStatusData(shipmentItems)} />
        </ChartCard>

        <ChartCard
          title="Alert Severity"
          description="Open and acknowledged alerts by severity"
          isLoading={alerts.isLoading}
          isError={alerts.isError}
          isEmpty={alertItems.length === 0}
          onRetry={() => void alerts.refetch()}
          emptyMessage="No alerts recorded"
        >
          <AlertSeverityChart data={alertSeverityData(alertItems)} />
        </ChartCard>

        <ChartCard
          title="Vehicle Utilisation"
          description="Fleet status breakdown"
          isLoading={vehicles.isLoading}
          isError={vehicles.isError}
          isEmpty={vehicleItems.length === 0}
          onRetry={() => void vehicles.refetch()}
          emptyMessage="No vehicles recorded"
        >
          <VehicleUtilizationChart data={vehicleUtilizationData(vehicleItems)} />
        </ChartCard>

        <ChartCard
          title="Temperature Trend"
          description="Predicted temperature envelope over time"
          isLoading={predictions.isLoading}
          isError={predictions.isError}
          isEmpty={predictionItems.length === 0}
          onRetry={() => void predictions.refetch()}
          emptyMessage="No predictions recorded"
        >
          <TemperatureTrendChart data={temperatureTrendData(predictionItems)} />
        </ChartCard>
      </section>
    </div>
  );
}
