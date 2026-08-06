"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface VehicleUtilizationDatum {
  name: string;
  value: number;
}

const COLORS: Record<string, string> = {
  active: "hsl(142 71% 45%)",
  maintenance: "hsl(38 92% 50%)",
  retired: "hsl(var(--muted-foreground))",
};

export function VehicleUtilizationChart({
  data,
}: {
  data: VehicleUtilizationDatum[];
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <XAxis
          dataKey="name"
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
          tickLine={false}
          axisLine={false}
          width={32}
        />
        <Tooltip cursor={{ fill: "hsl(var(--muted) / 0.5)" }} />
        <Bar dataKey="value" name="Vehicles" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name] ?? "hsl(var(--secondary))"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
