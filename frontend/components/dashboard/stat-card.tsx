"use client";

import type { LucideIcon } from "lucide-react";
import { AlertTriangle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
  title: string;
  icon: LucideIcon;
  value?: number;
  detail?: string;
  isLoading?: boolean;
  isError?: boolean;
  onRetry?: () => void;
}

/**
 * Single dashboard stat widget. Renders a loading skeleton while a query is
 * in flight, an inline retryable error when it fails, and the value otherwise.
 */
export function StatCard({
  title,
  icon: Icon,
  value,
  detail,
  isLoading,
  isError,
  onRetry,
}: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Icon className="size-4 shrink-0" aria-hidden />
          {title}
        </div>

        {isLoading ? (
          <div className="mt-3 h-8 w-16 animate-pulse rounded-md bg-muted" />
        ) : isError ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-destructive">
            <AlertTriangle className="size-4 shrink-0" aria-hidden />
            <span className="min-w-0 flex-1">Failed to load</span>
            {onRetry && (
              <Button
                variant="ghost"
                size="icon"
                className="size-7"
                onClick={onRetry}
                aria-label={`Retry ${title}`}
              >
                <RefreshCw className="size-4" aria-hidden />
              </Button>
            )}
          </div>
        ) : (
          <div className="mt-2">
            <p className="text-3xl font-bold tabular-nums tracking-tight">
              {value ?? 0}
            </p>
            {detail ? (
              <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
