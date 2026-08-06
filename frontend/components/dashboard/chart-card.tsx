"use client";

import type { ReactNode } from "react";

import { PageState } from "@/components/dashboard/page-state";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ChartCardProps {
  title: string;
  description?: string;
  isLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  onRetry?: () => void;
  emptyMessage?: string;
  children?: ReactNode;
}

/** Standardised chart widget: header, then a state-aware body. */
export function ChartCard({
  title,
  description,
  isLoading,
  isError,
  isEmpty,
  onRetry,
  emptyMessage,
  children,
}: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        {description ? (
          <CardDescription>{description}</CardDescription>
        ) : null}
      </CardHeader>
      <CardContent>
        <PageState
          isLoading={isLoading}
          isError={isError}
          isEmpty={isEmpty}
          onRetry={onRetry}
          emptyMessage={emptyMessage}
        >
          {children}
        </PageState>
      </CardContent>
    </Card>
  );
}
