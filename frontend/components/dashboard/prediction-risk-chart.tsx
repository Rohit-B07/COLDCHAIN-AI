"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export interface PredictionRiskDatum {
  name: string;
  value: number;
}

const RISK_COLORS: Record<string, string> = {
  low: "hsl(142 71% 45%)",
  medium: "hsl(38 92% 50%)",
  high: "hsl(262 83% 58%)",
  critical: "hsl(var(--destructive))",
};

export function PredictionRiskChart({ data }: { data: PredictionRiskDatum[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={50}
          outerRadius={90}
          paddingAngle={2}
          strokeWidth={2}
          isAnimationActive={false}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={RISK_COLORS[entry.name] ?? "hsl(var(--muted-foreground))"}
              stroke="hsl(var(--card))"
            />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}
