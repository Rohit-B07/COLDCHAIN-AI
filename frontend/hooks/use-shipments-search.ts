"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { Page, ShipmentQuery, ShipmentRead } from "@/lib/types";

function buildQueryString(query: ShipmentQuery) {
  const params = new URLSearchParams();
  const entries = Object.entries(query) as [
    keyof ShipmentQuery,
    string | number | undefined,
  ][];
  for (const [key, value] of entries) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * Paginated, filterable shipment list backed by `/shipments`.
 *
 * `placeholderData: keepPreviousData` keeps the previous page visible while a
 * new filter is applied, so the table updates in place without a page reload.
 */
export function useShipmentsSearch(query: ShipmentQuery) {
  return useQuery({
    queryKey: ["shipments", "search", query],
    queryFn: () =>
      apiClient.get<Page<ShipmentRead>>(`/shipments${buildQueryString(query)}`),
    placeholderData: keepPreviousData,
  });
}
