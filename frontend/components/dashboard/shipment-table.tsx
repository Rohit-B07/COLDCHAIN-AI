"use client";

import type { ShipmentRead } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  created: "hsl(220 14% 50%)",
  predicted: "hsl(262 83% 58%)",
  dispatched: "hsl(217 91% 60%)",
  in_transit: "hsl(199 89% 48%)",
  delivered: "hsl(142 71% 45%)",
  cancelled: "hsl(var(--destructive))",
};

function formatDateTime(value: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ShipmentTable({ items }: { items: ShipmentRead[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="pb-2 pr-4 font-medium">Tracking</th>
            <th className="pb-2 pr-4 font-medium">Vaccine</th>
            <th className="pb-2 pr-4 font-medium">Status</th>
            <th className="pb-2 pr-4 font-medium">Priority</th>
            <th className="pb-2 pr-4 font-medium">Doses</th>
            <th className="pb-2 pr-4 font-medium">Est. delivery</th>
            <th className="pb-2 font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {items.map((shipment) => (
            <tr key={shipment.id} className="border-b last:border-0">
              <td className="py-2 pr-4 font-mono text-xs">
                {shipment.tracking_code}
              </td>
              <td className="py-2 pr-4">{shipment.vaccine_name}</td>
              <td className="py-2 pr-4">
                <span className="inline-flex items-center gap-1.5">
                  <span
                    className="size-2 rounded-full"
                    style={{
                      backgroundColor:
                        STATUS_COLORS[shipment.status] ??
                        "hsl(var(--muted-foreground))",
                    }}
                    aria-hidden
                  />
                  <span className="capitalize">
                    {shipment.status.replace("_", " ")}
                  </span>
                </span>
              </td>
              <td className="py-2 pr-4 capitalize">{shipment.priority}</td>
              <td className="py-2 pr-4 tabular-nums">
                {shipment.dose_count.toLocaleString()}
              </td>
              <td className="py-2 pr-4 text-muted-foreground">
                {formatDateTime(shipment.estimated_delivery_at)}
              </td>
              <td className="py-2 text-muted-foreground">
                {formatDateTime(shipment.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
