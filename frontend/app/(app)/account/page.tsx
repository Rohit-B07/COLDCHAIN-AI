"use client";

import { LogoutButton } from "@/components/auth/logout-button";
import { useAuth } from "@/components/providers/auth-provider";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function AccountPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Account</h1>
          <p className="text-sm text-muted-foreground">
            Your session and profile
          </p>
        </div>
        <LogoutButton />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Signed-in user details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <dl className="grid grid-cols-[120px_1fr] gap-y-2">
            <dt className="font-medium text-muted-foreground">Name</dt>
            <dd>{user?.full_name ?? "—"}</dd>
            <dt className="font-medium text-muted-foreground">Email</dt>
            <dd>{user?.email ?? "—"}</dd>
            <dt className="font-medium text-muted-foreground">Role</dt>
            <dd>{user?.role ?? "—"}</dd>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
