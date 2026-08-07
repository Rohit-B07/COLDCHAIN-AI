"use client";

import { FormEvent, useState } from "react";
import { RotateCcw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type {
  PriorityLevel,
  ShipmentQuery,
  ShipmentSortField,
  ShipmentSortOrder,
  ShipmentStatus,
} from "@/lib/types";

const STATUS_OPTIONS: ShipmentStatus[] = [
  "created",
  "predicted",
  "dispatched",
  "in_transit",
  "delivered",
  "cancelled",
];

const PRIORITY_OPTIONS: PriorityLevel[] = ["low", "medium", "high"];

const SORT_FIELDS: { value: ShipmentSortField; label: string }[] = [
  { value: "created_at", label: "Created" },
  { value: "tracking_code", label: "Tracking code" },
  { value: "status", label: "Status" },
  { value: "priority", label: "Priority" },
  { value: "vaccine_name", label: "Vaccine" },
  { value: "estimated_delivery_at", label: "Est. delivery" },
];

const SORT_ORDERS: { value: ShipmentSortOrder; label: string }[] = [
  { value: "desc", label: "Newest first" },
  { value: "asc", label: "Oldest first" },
];

interface Draft {
  search: string;
  status: ShipmentStatus | "";
  priority: PriorityLevel | "";
  vaccine_type: string;
  created_after: string;
  created_before: string;
  expected_delivery_after: string;
  expected_delivery_before: string;
  sort_by: ShipmentSortField;
  sort_order: ShipmentSortOrder;
}

const DEFAULTS: Draft = {
  search: "",
  status: "",
  priority: "",
  vaccine_type: "",
  created_after: "",
  created_before: "",
  expected_delivery_after: "",
  expected_delivery_before: "",
  sort_by: "created_at",
  sort_order: "desc",
};

function toDateInput(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toISOString().slice(0, 10);
}

function fromQuery(query: ShipmentQuery): Draft {
  return {
    search: query.search ?? "",
    status: query.status ?? "",
    priority: query.priority ?? "",
    vaccine_type: query.vaccine_type ?? "",
    created_after: toDateInput(query.created_after),
    created_before: toDateInput(query.created_before),
    expected_delivery_after: toDateInput(query.expected_delivery_after),
    expected_delivery_before: toDateInput(query.expected_delivery_before),
    sort_by: query.sort_by ?? "created_at",
    sort_order: query.sort_order ?? "desc",
  };
}

function buildQuery(draft: Draft): ShipmentQuery {
  return {
    search: draft.search.trim() || undefined,
    status: draft.status || undefined,
    priority: draft.priority || undefined,
    vaccine_type: draft.vaccine_type.trim() || undefined,
    created_after: draft.created_after
      ? `${draft.created_after}T00:00:00.000Z`
      : undefined,
    created_before: draft.created_before
      ? `${draft.created_before}T23:59:59.999Z`
      : undefined,
    expected_delivery_after: draft.expected_delivery_after
      ? `${draft.expected_delivery_after}T00:00:00.000Z`
      : undefined,
    expected_delivery_before: draft.expected_delivery_before
      ? `${draft.expected_delivery_before}T23:59:59.999Z`
      : undefined,
    sort_by: draft.sort_by,
    sort_order: draft.sort_order,
    page: 1,
    size: 10,
  };
}

interface ShipmentSearchPanelProps {
  value: ShipmentQuery;
  onChange: (next: ShipmentQuery) => void;
}

/**
 * Reusable search and filtering controls for the shipment table. The panel
 * keeps an editable draft locally and only notifies the parent when a search
 * is applied, so the table updates in place without a page refresh.
 */
export function ShipmentSearchPanel({
  value,
  onChange,
}: ShipmentSearchPanelProps) {
  const [draft, setDraft] = useState<Draft>(() => fromQuery(value));

  const update = (patch: Partial<Draft>) =>
    setDraft((previous) => ({ ...previous, ...patch }));

  const apply = (event: FormEvent) => {
    event.preventDefault();
    onChange(buildQuery(draft));
  };

  const reset = () => {
    setDraft(DEFAULTS);
    onChange(buildQuery(DEFAULTS));
  };

  return (
    <form onSubmit={apply} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div className="space-y-1.5">
        <Label htmlFor="shipment-search">Keyword</Label>
        <Input
          id="shipment-search"
          placeholder="Tracking code or vaccine"
          value={draft.search}
          onChange={(event) => update({ search: event.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-status">Status</Label>
        <select
          id="shipment-status"
          className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={draft.status}
          onChange={(event) =>
            update({ status: event.target.value as ShipmentStatus | "" })
          }
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-priority">Priority</Label>
        <select
          id="shipment-priority"
          className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={draft.priority}
          onChange={(event) =>
            update({ priority: event.target.value as PriorityLevel | "" })
          }
        >
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-vaccine">Vaccine</Label>
        <Input
          id="shipment-vaccine"
          placeholder="e.g. Pfizer-BioNTech"
          value={draft.vaccine_type}
          onChange={(event) => update({ vaccine_type: event.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-created-after">Created after</Label>
        <Input
          id="shipment-created-after"
          type="date"
          value={draft.created_after}
          onChange={(event) => update({ created_after: event.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-created-before">Created before</Label>
        <Input
          id="shipment-created-before"
          type="date"
          value={draft.created_before}
          onChange={(event) => update({ created_before: event.target.value })}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-due-after">Est. delivery after</Label>
        <Input
          id="shipment-due-after"
          type="date"
          value={draft.expected_delivery_after}
          onChange={(event) =>
            update({ expected_delivery_after: event.target.value })
          }
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-due-before">Est. delivery before</Label>
        <Input
          id="shipment-due-before"
          type="date"
          value={draft.expected_delivery_before}
          onChange={(event) =>
            update({ expected_delivery_before: event.target.value })
          }
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-sort-by">Sort by</Label>
        <select
          id="shipment-sort-by"
          className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={draft.sort_by}
          onChange={(event) =>
            update({ sort_by: event.target.value as ShipmentSortField })
          }
        >
          {SORT_FIELDS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="shipment-sort-order">Order</Label>
        <select
          id="shipment-sort-order"
          className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={draft.sort_order}
          onChange={(event) =>
            update({ sort_order: event.target.value as ShipmentSortOrder })
          }
        >
          {SORT_ORDERS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-end gap-2">
        <Button type="submit">
          <Search aria-hidden />
          Search
        </Button>
        <Button type="button" variant="outline" onClick={reset}>
          <RotateCcw aria-hidden />
          Reset
        </Button>
      </div>
    </form>
  );
}
