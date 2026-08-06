"use client";

import { Loader2, LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/use-auth-forms";

interface LogoutButtonProps {
  className?: string;
}

export function LogoutButton({ className }: LogoutButtonProps) {
  const { logout, mutation } = useLogout();

  return (
    <Button
      variant="outline"
      className={className}
      onClick={logout}
      disabled={mutation.isPending}
    >
      {mutation.isPending ? (
        <Loader2 className="size-4 animate-spin" aria-hidden />
      ) : (
        <LogOut className="size-4" aria-hidden />
      )}
      Sign out
    </Button>
  );
}
