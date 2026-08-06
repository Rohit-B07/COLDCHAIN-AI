"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export interface ShipmentStatusDatum {
  name: string;
  value: number;
}

const COLORS = [
  "hsl(var(--primary))",
  "hsl(38 92% 50%)",
  "hsl(142 71% 45%)",
  "hsl(262 83% 58%)",
  "hsl(var(--destructive))",
];

export function ShipmentStatusChart({ data }: { data: ShipmentStatusDatum[] }) {
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
          {data.map((entry, index) => (
            <Cell
              key={entry.name}
              fill={COLORS[index % COLORS.length]}
              stroke="hsl(var(--card))"
            />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}
