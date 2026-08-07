"use client";

import type { PredictionHistoryItem } from "@/lib/types";

const RISK_COLORS: Record<string, string> = {
  low: "hsl(142 71% 45%)",
  medium: "hsl(38 92% 50%)",
  high: "hsl(262 83% 58%)",
  critical: "hsl(var(--destructive))",
};

function shortId(id: string) {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function PredictionHistoryTable({
  items,
}: {
  items: PredictionHistoryItem[];
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
            <th className="pb-2 pr-4 font-medium">Shipment</th>
            <th className="pb-2 pr-4 font-medium">Risk</th>
            <th className="pb-2 pr-4 font-medium">Confidence</th>
            <th className="pb-2 pr-4 font-medium">Weather</th>
            <th className="pb-2 font-medium">Predicted</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b last:border-0">
              <td className="py-2 pr-4 font-mono text-xs text-muted-foreground">
                {shortId(item.shipment_id)}
              </td>
              <td className="py-2 pr-4">
                <span
                  className="inline-flex items-center gap-1.5"
                  title={item.weather_summary}
                >
                  <span
                    className="size-2 rounded-full"
                    style={{
                      backgroundColor:
                        RISK_COLORS[item.risk_level] ??
                        "hsl(var(--muted-foreground))",
                    }}
                    aria-hidden
                  />
                  <span className="capitalize">{item.risk_level}</span>
                  <span className="text-xs tabular-nums text-muted-foreground">
                    {Math.round(item.risk_score * 100)}%
                  </span>
                </span>
              </td>
              <td className="py-2 pr-4 tabular-nums">
                {Math.round(item.confidence * 100)}%
              </td>
              <td className="py-2 pr-4 text-muted-foreground">
                {item.weather_summary}
              </td>
              <td className="py-2 text-muted-foreground">
                {formatDateTime(item.predicted_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
