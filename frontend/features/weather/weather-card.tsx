"use client";

import { useWeather } from "@/hooks/use-weather";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface WeatherCardProps {
  latitude?: number;
  longitude?: number;
}

export function WeatherCard({ latitude, longitude }: WeatherCardProps) {
  const { weather, loading, error, refresh } = useWeather(latitude, longitude);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Local Weather</CardTitle>
        <CardDescription>
          Current conditions for the selected location
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {loading ? (
          <p className="text-muted-foreground">Loading&hellip;</p>
        ) : weather ? (
          <>
            <p className="flex items-center gap-2">
              <span
                className={`inline-block size-2 rounded-full ${
                  weather.is_mock ? "bg-amber-500" : "bg-blue-500"
                }`}
                aria-hidden
              />
              {weather.condition} · {weather.temperature_c}°C
            </p>
            <p>
              Humidity: {weather.humidity_pct}% · Wind: {weather.wind_kmh} km/h
            </p>
            <p>Precipitation: {weather.precipitation_mm} mm</p>
            <p className="text-muted-foreground">
              Source: {weather.source}
              {weather.is_mock ? " (mock)" : ""}
            </p>
            {latitude !== undefined && longitude !== undefined ? (
              <button
                type="button"
                onClick={() => void refresh()}
                className="text-xs text-blue-600 underline"
              >
                Refresh
              </button>
            ) : null}
          </>
        ) : (
          <p className="text-muted-foreground">No location selected.</p>
        )}
        {error ? <p className="text-destructive">{error}</p> : null}
      </CardContent>
    </Card>
  );
}
