"use client";

import { useCallback, useEffect, useState } from "react";

import { apiClient, ApiError } from "@/lib/api/client";
import type { WeatherRead } from "@/lib/types";

interface UseWeatherResult {
  weather: WeatherRead | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Fetch the current weather for a location from the backend `/weather`
 * endpoint. `undefined` coordinates keep the hook idle (no request fired).
 */
export function useWeather(
  latitude?: number,
  longitude?: number,
): UseWeatherResult {
  const [weather, setWeather] = useState<WeatherRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (latitude === undefined || longitude === undefined) {
      setWeather(null);
      return;
    }
    setLoading(true);
    try {
      const result = await apiClient.get<WeatherRead>(
        `/weather?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`,
      );
      setWeather(result);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Unable to fetch weather",
      );
    } finally {
      setLoading(false);
    }
  }, [latitude, longitude]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { weather, loading, error, refresh };
}
