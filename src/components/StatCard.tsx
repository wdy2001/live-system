import type { ReactNode } from "react";

type StatCardVariant = "blue" | "green" | "orange";

interface StatCardProps {
  icon: ReactNode;
  title: string;
  value: string | number;
  subValue?: string;
  variant?: StatCardVariant;
}

const VARIANT_STYLES: Record<StatCardVariant, { bg: string; text: string }> = {
  blue: { bg: "bg-blue-50", text: "text-blue-600" },
  green: { bg: "bg-emerald-50", text: "text-emerald-600" },
  orange: { bg: "bg-amber-50", text: "text-amber-600" },
};

export default function StatCard({
  icon,
  title,
  value,
  subValue,
  variant = "blue",
}: StatCardProps) {
  const styles = VARIANT_STYLES[variant];

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-2 text-gray-800">{value}</p>
          {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
        </div>
        <div
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${styles.bg} ${styles.text}`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
