"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

import { cn } from "@/lib/utils";

const CRUMB_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  account: "Account",
  shipments: "Shipments",
  routes: "Routes",
  predictions: "Predictions",
  alerts: "Alerts",
  warehouses: "Warehouses",
  phcs: "Health Centres",
  users: "Users",
};

/** Breadcrumb trail derived from the current route segment. */
export function Breadcrumbs({ className }: { className?: string }) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const crumbs = segments.map((segment) => ({
    href: `/${segment}`,
    label: CRUMB_LABELS[segment] ?? segment,
  }));

  return (
    <nav aria-label="Breadcrumb" className={cn("min-w-0", className)}>
      <ol className="flex items-center gap-1.5 text-sm">
        <li>
          <Link
            href="/dashboard"
            className="flex items-center gap-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <Home className="size-3.5" aria-hidden />
            <span className="sr-only">Home</span>
          </Link>
        </li>
        {crumbs.map((crumb, index) => {
          const isLast = index === crumbs.length - 1;
          return (
            <li key={crumb.href} className="flex min-w-0 items-center gap-1.5">
              <ChevronRight className="size-3.5 shrink-0 text-muted-foreground/50" aria-hidden />
              {isLast ? (
                <span className="truncate font-medium text-foreground">
                  {crumb.label}
                </span>
              ) : (
                <Link
                  href={crumb.href}
                  className="truncate text-muted-foreground transition-colors hover:text-foreground"
                >
                  {crumb.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
