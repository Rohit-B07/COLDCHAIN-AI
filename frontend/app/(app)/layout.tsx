import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { RouteGuard } from "@/components/route-guard";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteGuard>
      <DashboardShell>{children}</DashboardShell>
    </RouteGuard>
  );
}
