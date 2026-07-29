import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";
import { UTILITY_META } from "@/lib/constants";
import type { UtilityType } from "@/types";
import { BarChart3 } from "lucide-react";

interface TrendItem {
  period: string;
  usage: Record<UtilityType, number>;
}

const COLORS: Record<UtilityType, string> = {
  electricity: "#D97706",
  water: "#0891B2",
  gas: "#EA580C",
};

export default function UsageChart({ data }: { data: TrendItem[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[280px] flex-col items-center justify-center text-center">
        <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-forest-50">
          <BarChart3 className="h-7 w-7 text-forest-400" />
        </div>
        <p className="text-sm text-ink-muted">暂无用量数据</p>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    period: d.period.slice(5),
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
