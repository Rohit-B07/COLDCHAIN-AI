"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Loader2 } from "lucide-react";

interface RouteGuardProps {
  children: ReactNode;
  allowedRoles?: string[];
  redirectTo?: string;
}

/**
 * Guards protected routes.
 *
 * Renders a loading state while the session is being validated, redirects
 * unauthenticated users to the login page, and enforces optional role
 * restrictions for the current user.
 */
export function RouteGuard({
  children,
  allowedRoles,
  redirectTo = "/login",
}: RouteGuardProps) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace(redirectTo);
      return;
    }
    if (allowedRoles && user && !allowedRoles.includes(user.role)) {
      router.replace("/");
    }
  }, [isLoading, isAuthenticated, user, allowedRoles, redirectTo, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (allowedRoles && user && !allowedRoles.includes(user.role)) return null;

  return <>{children}</>;
}
