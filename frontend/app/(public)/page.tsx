import { HealthStatusCard } from "@/features/health";
import { siteConfig } from "@/lib/config";

export default function HomePage() {
  return (
    <div className="container max-w-5xl py-12">
      <section className="space-y-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          {siteConfig.name}
        </h1>
        <p className="mx-auto max-w-2xl text-muted-foreground">
          {siteConfig.description}
        </p>
      </section>

      <section className="mt-12 grid gap-6 md:grid-cols-3">
        <HealthStatusCard />
      </section>
    </div>
  );
}
