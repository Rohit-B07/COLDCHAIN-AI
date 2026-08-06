/**
 * Typed API client for the ColdChain AI backend.
 *
 * Encapsulates fetch, error handling, and the standard response envelope so
 * that feature code only deals with typed domain objects. Swap the fetch
 * implementation here without touching callers.
 */

import { apiUrl } from "@/lib/config";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message =
      payload?.message ?? `Request failed with status ${response.status}`;
    throw new ApiError(
      response.status,
      payload?.error_code ?? "unknown",
      message,
    );
  }

  const envelope = (await response.json()) as ApiEnvelope<T>;
  return envelope.data as T;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
