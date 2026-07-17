import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  icon: LucideIcon;
  accent: "forest" | "energy" | "aqua" | "clay";
  delay?: number;
}

const ACCENT: Record<StatCardProps["accent"], { bg: string; text: string; ring: string }> = {
  forest: { bg: "bg-forest-50", text: "text-forest-600", ring: "ring-forest-100" },
  energy: { bg: "bg-energy-50", text: "text-energy-600", ring: "ring-energy-100" },
  aqua: { bg: "bg-aqua-50", text: "text-aqua-500", ring: "ring-aqua-100" },
  clay: { bg: "bg-clay-50", text: "text-clay-500", ring: "ring-clay-100" },
};

export default function StatCard({ label, value, hint, icon: Icon, accent, delay = 0 }: StatCardProps) {
  const a = ACCENT[accent];
  return (
    <div
      className="card card-hover animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-sm text-ink-muted">{label}</p>
          <p className="mt-2 font-serif text-2xl font-bold text-ink">{value}</p>
          {hint && <p className="mt-1 text-xs text-ink-muted">{hint}</p>}
        </div>
        <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ring-1", a.bg, a.text, a.ring)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}
