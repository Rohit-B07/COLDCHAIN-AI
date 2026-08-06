"use client";

import { useHealth } from "@/hooks/use-health";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function HealthStatusCard() {
  const { healthy, database, loading, error } = useHealth();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Backend Status</CardTitle>
        <CardDescription>Connectivity to the ColdChain AI API</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {loading ? (
          <p className="text-muted-foreground">Checking&hellip;</p>
        ) : (
          <>
            <p className="flex items-center gap-2">
              <span
                className={`inline-block size-2 rounded-full ${
                  healthy ? "bg-green-500" : "bg-red-500"
                }`}
                aria-hidden
              />
              API: {healthy ? "Online" : "Offline"}
            </p>
            <p>
              Database:{" "}
              {database === "ok" ? "Connected" : (database ?? "Unknown")}
            </p>
            {error ? <p className="text-destructive">{error}</p> : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
