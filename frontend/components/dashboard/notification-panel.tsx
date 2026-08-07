"use client";

import { AlertTriangle, Bell, Sparkles, Truck } from "lucide-react";

import type { NotificationItem, NotificationType } from "@/lib/types";

const SEVERITY_STYLES: Record<string, string> = {
  info: "bg-primary/10 text-primary",
  warning: "bg-amber-500/10 text-amber-500",
  critical: "bg-destructive/10 text-destructive",
};

const TYPE_ICONS: Record<NotificationType, typeof Bell> = {
  prediction: Sparkles,
  alert: AlertTriangle,
  shipment: Truck,
  system: Bell,
};

function shortId(id: string) {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id;
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function NotificationPanel({ items }: { items: NotificationItem[] }) {
  return (
    <ul className="divide-y" aria-label="Notifications">
      {items.map((item) => {
        const Icon = TYPE_ICONS[item.type] ?? Bell;
        return (
          <li
            key={item.id}
            className={`flex items-start gap-3 py-3 ${item.read ? "opacity-60" : ""}`}
          >
            <span
              className={`mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md ${SEVERITY_STYLES[item.severity] ?? "bg-muted text-muted-foreground"}`}
            >
              <Icon className="size-4" aria-hidden />
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <p className="truncate text-sm font-medium">{item.title}</p>
                <time
                  className="shrink-0 text-xs text-muted-foreground"
                  dateTime={item.created_at}
                >
                  {formatTimestamp(item.created_at)}
                </time>
              </div>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {item.message}
              </p>
              <div className="mt-1 flex items-center gap-2 text-xs">
                <span
                  className={`inline-flex rounded-full px-2 py-0.5 capitalize ${SEVERITY_STYLES[item.severity] ?? "bg-muted text-muted-foreground"}`}
                >
                  {item.severity}
                </span>
                {item.shipment_id ? (
                  <span className="font-mono text-muted-foreground">
                    {shortId(item.shipment_id)}
                  </span>
                ) : null}
                {!item.read ? (
                  <span className="text-muted-foreground" aria-label="Unread">
                    Unread
                  </span>
                ) : null}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

/** Small summary line used by the Notification Center card header. */
export function NotificationSummary({
  total,
  unread,
}: {
  total: number;
  unread: number;
}) {
  return (
    <p className="text-sm text-muted-foreground">
      <span className="font-semibold tabular-nums text-foreground">
        {total}
      </span>{" "}
      notifications ·{" "}
      <span className="font-semibold tabular-nums text-foreground">
        {unread}
      </span>{" "}
      unread
    </p>
  );
}
