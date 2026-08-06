"use client";

import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

interface PageStateProps {
  isLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  onRetry?: () => void;
  emptyMessage?: string;
  height?: string;
  children?: ReactNode;
}

/**
 * Shared stateful container for dashboard widgets. Coordinates the four
 * visual states a widget can be in: loading, error, empty and content.
 */
export function PageState({
  isLoading,
  isError,
  isEmpty,
  onRetry,
  emptyMessage = "No data available",
  height = "h-64",
  children,
}: PageStateProps) {
  return (
    <div className={`flex ${height} items-center justify-center rounded-md`}>
      {isLoading ? (
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-hidden />
      ) : isError ? (
        <div className="flex flex-col items-center gap-3 text-center">
          <AlertTriangle className="size-6 text-destructive" aria-hidden />
          <p className="text-sm text-muted-foreground">Failed to load data</p>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="size-4" aria-hidden />
              Retry
            </Button>
          )}
        </div>
      ) : isEmpty ? (
        <div className="flex flex-col items-center gap-2 text-center text-muted-foreground">
          <Inbox className="size-6" aria-hidden />
          <p className="text-sm">{emptyMessage}</p>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
