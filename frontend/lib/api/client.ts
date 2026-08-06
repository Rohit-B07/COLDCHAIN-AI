/**
 * Typed API client for the ColdChain AI backend.
 *
 * Thin wrapper over the shared Axios instance that unwraps the standard
 * response envelope (`{ success, data }`) so feature code only deals with
 * typed domain objects.
 */

import type { AxiosRequestConfig } from "axios";

import { axiosClient } from "@/lib/api/axios";
import type { ApiEnvelope } from "@/lib/types";

export { ApiError, UNAUTHORIZED_EVENT } from "@/lib/api/axios";
export type { ApiErrorDetail } from "@/lib/types";

async function request<T>(
  path: string,
  config: AxiosRequestConfig = {},
): Promise<T> {
  const response = await axiosClient.request<ApiEnvelope<T>>({
    url: path,
    ...config,
  });
  const envelope = response.data;
  if (envelope.data === null) {
    throw new TypeError("API response did not include a data payload");
  }
  return envelope.data as T;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", data: body }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", data: body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  request: <T>(path: string, config: AxiosRequestConfig) =>
    request<T>(path, config),
};
