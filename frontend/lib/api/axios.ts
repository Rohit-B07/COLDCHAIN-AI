import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import { clearSession, getAccessToken } from "@/lib/auth/session";
import { apiConfig } from "@/lib/config";
import type { ApiErrorDetail, ApiErrorResponse } from "@/lib/types";

/**
 * Shared Axios instance.
 *
 * Centralises base URL, authentication header injection and uniform error
 * normalisation so feature code only deals with typed domain objects.
 */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: ApiErrorDetail[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Event dispatched when the backend rejects the access token. */
export const UNAUTHORIZED_EVENT = "coldchain:unauthorized";

function getErrorMessage(
  payload: ApiErrorResponse | undefined,
  fallback: string,
): string {
  if (payload?.message) return payload.message;
  return fallback;
}

export const axiosClient: AxiosInstance = axios.create({
  baseURL: apiConfig.baseUrl,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

axiosClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    const status = error.response?.status ?? 0;
    const payload = error.response?.data;

    if (status === 401) {
      clearSession();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
      }
    }

    return Promise.reject(
      new ApiError(
        status,
        payload?.error_code ?? "unknown_error",
        getErrorMessage(payload, error.message || "Request failed"),
        payload?.details ?? [],
      ),
    );
  },
);
