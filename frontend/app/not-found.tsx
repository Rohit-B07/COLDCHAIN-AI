import Link from "next/link";
import { Compass } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
      <Compass className="size-10 text-muted-foreground" aria-hidden />
      <p className="text-5xl font-bold tracking-tight">404</p>
      <h2 className="text-lg font-semibold">Page not found</h2>
      <p className="max-w-md text-sm text-muted-foreground">
        The page you are looking for does not exist or may have been moved.
      </p>
      <Button asChild>
        <Link href="/">Back to home</Link>
      </Button>
    </div>
  );
}
