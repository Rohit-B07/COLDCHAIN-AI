import type { TokenResponse, User } from "@/lib/types";

/**
 * Client-side session persistence.
 *
 * Tokens and the cached user profile are stored in `localStorage` so the
 * authentication provider can restore a session without an extra round trip
 * and the Axios interceptor can attach the bearer token to every request.
 */

const ACCESS_TOKEN_KEY = "coldchain.access_token";
const REFRESH_TOKEN_KEY = "coldchain.refresh_token";
const USER_KEY = "coldchain.user";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function saveSession(tokens: TokenResponse): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(tokens.user));
}

export function saveAccessToken(accessToken: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}
