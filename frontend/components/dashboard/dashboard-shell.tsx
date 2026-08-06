"use client";

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

import { Breadcrumbs } from "@/components/dashboard/breadcrumbs";
import { UserMenu } from "@/components/dashboard/user-menu";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { SiteFooter } from "@/components/layout/site-footer";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DashboardShellProps {
  children: React.ReactNode;
}

/**
 * Authenticated application shell.
 *
 * Desktop shows a persistent sidebar; mobile collapses it into a slide-over
 * drawer driven by the hamburger button in the top bar. The top bar hosts
 * breadcrumbs, a theme-agnostic spacer and the user profile menu.
 */
export function DashboardShell({ children }: DashboardShellProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const close = () => setMobileOpen(false);
    window.addEventListener("resize", close);
    return () => window.removeEventListener("resize", close);
  }, []);

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <AppSidebar className="hidden lg:flex" />

      {/* Mobile drawer */}
      <div
        className={cn(
          "fixed inset-0 z-50 lg:hidden",
          mobileOpen ? "pointer-events-auto" : "pointer-events-none",
        )}
        aria-hidden={!mobileOpen}
      >
        <div
          className={cn(
            "absolute inset-0 bg-background/80 backdrop-blur-sm transition-opacity",
            mobileOpen ? "opacity-100" : "opacity-0",
          )}
          onClick={() => setMobileOpen(false)}
        />
        <div
          className={cn(
            "absolute inset-y-0 left-0 flex transition-transform duration-200",
            mobileOpen ? "translate-x-0" : "-translate-x-full",
          )}
        >
          <AppSidebar />
          <Button
            variant="ghost"
            size="icon"
            className="absolute -right-12 top-3 text-muted-foreground hover:bg-muted"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X className="size-5" aria-hidden />
          </Button>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur sm:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="size-5" aria-hidden />
          </Button>
          <Breadcrumbs className="flex-1" />
          <UserMenu />
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto max-w-7xl px-4 py-8 sm:px-6">
            {children}
          </div>
        </main>

        <SiteFooter />
      </div>
    </div>
  );
}
