import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";
import { UTILITY_META } from "@/lib/constants";
import type { UtilityType } from "@/types";

interface TrendItem {
  period: string;
  usage: Record<UtilityType, number>;
}

const COLORS: Record<UtilityType, string> = {
  electricity: "#D97706",
  water: "#0E7490",
  gas: "#B45309",
};

export default function UsageChart({ data }: { data: TrendItem[] }) {
  const chartData = data.map((d) => ({
    period: d.period.slice(5), // MM
    电费: Number(d.usage.electricity.toFixed(1)),
    水费: Number(d.usage.water.toFixed(1)),
    燃气: Number(d.usage.gas.toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} barGap={4} barCategoryGap="22%">
        <CartesianGrid strokeDasharray="3 3" stroke="#ECFDF3" vertical={false} />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 12, fill: "#6B7670" }}
          axisLine={{ stroke: "#D1FAE0" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: "#6B7670" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: "1px solid #D1FAE0",
            boxShadow: "0 8px 24px rgba(15,81,50,0.10)",
            fontSize: 13,
          }}
          cursor={{ fill: "#ECFDF3" }}
        />
        <Legend
          iconType="circle"
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
        {(["electricity", "water", "gas"] as UtilityType[]).map((t) => (
          <Bar
            key={t}
            dataKey={UTILITY_META[t].label.replace("费", "")}
            fill={COLORS[t]}
            radius={[4, 4, 0, 0]}
            maxBarSize={26}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
