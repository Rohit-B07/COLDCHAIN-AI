"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { apiClient, UNAUTHORIZED_EVENT } from "@/lib/api/client";
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  saveSession,
} from "@/lib/auth/session";
import type { TokenResponse, User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [isLoading, setIsLoading] = useState<boolean>(
    () => getAccessToken() !== null,
  );

  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () =>
      window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [handleUnauthorized]);

  useEffect(() => {
    if (getAccessToken() === null) {
      setIsLoading(false);
      return;
    }
    let active = true;
    const validate = async () => {
      try {
        const current = await apiClient.get<User>("/auth/me");
        if (active) setUser(current);
      } catch {
        if (active) {
          clearSession();
          setUser(null);
        }
      } finally {
        if (active) setIsLoading(false);
      }
    };
    void validate();
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiClient.post<TokenResponse>("/auth/login", {
      email,
      password,
    });
    saveSession(tokens);
    setUser(tokens.user);
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        await apiClient.post("/auth/logout", { refresh_token: refreshToken });
      } catch {
        // Session is cleared locally regardless of remote logout success.
      }
    }
    clearSession();
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return;
    await apiClient.post("/auth/refresh", { refresh_token: refreshToken });
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
      refresh,
    }),
    [user, isLoading, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
