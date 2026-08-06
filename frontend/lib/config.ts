/**
 * Shared frontend configuration.
 *
 * All environment-derived settings are read through this module so that
 * components and features never access `process.env` directly. Values are
 * inlined at build time by Next.js (NEXT_PUBLIC_* prefix).
 */

function requiredEnv(name: string, fallback: string): string {
  const value = process.env[name];
  return value ?? fallback;
}

export const siteConfig = {
  name: "ColdChain AI",
  description:
    "AI-powered decision support for vaccine cold-chain delivery: predict temperature excursions and plan safe routes.",
} as const;

export const apiConfig = {
  /** Base URL of the backend API, excluding the API version prefix. */
  baseUrl: requiredEnv(
    "NEXT_PUBLIC_API_BASE_URL",
    process.env.NODE_ENV === "production"
      ? "/api/v1"
      : "http://localhost:8000/api/v1",
  ),
  version: "v1",
} as const;
