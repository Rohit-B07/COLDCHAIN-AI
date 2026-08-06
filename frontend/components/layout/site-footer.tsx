import { cn } from "@/lib/utils";

interface SiteFooterProps {
  className?: string;
}

export function SiteFooter({ className }: SiteFooterProps) {
  return (
    <footer
      className={cn(
        "border-t bg-muted/40 py-6 text-center text-sm text-muted-foreground",
        className,
      )}
    >
      ColdChain AI &mdash; Smart India Hackathon prototype
    </footer>
  );
}
