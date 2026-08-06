"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import Link from "next/link";
import { ChevronDown, LogOut, UserRound } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { useLogout } from "@/hooks/use-auth-forms";
import { cn } from "@/lib/utils";

function initials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

/** User profile dropdown shown in the dashboard top bar. */
export function UserMenu() {
  const { user } = useAuth();
  const { logout, mutation } = useLogout();

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-full p-1 outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          aria-label="Open user menu"
        >
          <span className="flex size-8 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
            {initials(user?.full_name)}
          </span>
          <ChevronDown className="size-4 text-muted-foreground" aria-hidden />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 min-w-56 rounded-lg border bg-popover p-1 text-popover-foreground shadow-md"
        >
          <div className="px-2 py-1.5">
            <p className="truncate text-sm font-medium">{user?.full_name}</p>
            <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
            <p className="mt-1 inline-block rounded-full bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground">
              {user?.role?.replace("_", " ")}
            </p>
          </div>
          <DropdownMenu.Separator className="my-1 h-px bg-border" />

          <DropdownMenu.Item asChild>
            <Link
              href="/account"
              className={cn(
                "flex cursor-pointer select-none items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-none",
                "focus:bg-accent focus:text-accent-foreground",
              )}
            >
              <UserRound className="size-4" aria-hidden />
              Account
            </Link>
          </DropdownMenu.Item>

          <DropdownMenu.Item
            onSelect={logout}
            disabled={mutation.isPending}
            className={cn(
              "flex cursor-pointer select-none items-center gap-2 rounded-md px-2 py-1.5 text-sm outline-none",
              "focus:bg-destructive focus:text-destructive-foreground",
              mutation.isPending && "opacity-50",
            )}
          >
            <LogOut className="size-4" aria-hidden />
            {mutation.isPending ? "Signing out…" : "Sign out"}
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
