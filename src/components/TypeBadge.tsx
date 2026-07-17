import { cn } from "@/lib/utils";
import { UTILITY_META } from "@/lib/constants";
import type { UtilityType } from "@/types";

export default function TypeBadge({
  type, size = "md",
}: { type: UtilityType; size?: "sm" | "md" }) {
  const meta = UTILITY_META[type];
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-medium",
        meta.bg, meta.text,
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm",
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />
      {meta.label}
    </span>
  );
}
