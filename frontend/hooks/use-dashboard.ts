"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type {
  AlertRead,
  DriverRead,
  Page,
  PhcRead,
  PredictionRead,
  RouteRead,
  ShipmentRead,
  VehicleRead,
  WarehouseRead,
} from "@/lib/types";

/**
 * Dashboard data hooks.
 *
 * Each hook fetches a paginated list from the corresponding RBAC-protected
 * endpoint and derives summary figures the dashboard widgets render. All
 * queries are independent so a missing permission on one resource (e.g. a
 * driver without facility/logistics access) degrades that single widget
 * rather than the whole dashboard.
 */

const LIST_SIZE = 100;

function useList<T>(key: string, path: string) {
  return useQuery({
    queryKey: ["dashboard", key],
    queryFn: () => apiClient.get<Page<T>>(`${path}?size=${LIST_SIZE}`),
  });
}

export function useShipments() {
  return useList<ShipmentRead>("shipments", "/shipments");
}

export function useRoutes() {
  return useList<RouteRead>("routes", "/routes");
}

export function useWarehouses() {
  return useList<WarehouseRead>("warehouses", "/warehouses");
}

export function usePhcs() {
  return useList<PhcRead>("phcs", "/phcs");
}

export function useVehicles() {
  return useList<VehicleRead>("vehicles", "/vehicles");
}

export function useDrivers() {
  return useList<DriverRead>("drivers", "/drivers");
}

export function useAlerts() {
  return useList<AlertRead>("alerts", "/alerts");
}

export function usePredictions() {
  return useList<PredictionRead>("predictions", "/predictions");
}
