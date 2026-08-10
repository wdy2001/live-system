import { cn } from "@/lib/utils";

type BadgeType = "electricity" | "water" | "gas" | "other";

interface TypeBadgeProps {
  type: BadgeType;
}

const TYPE_STYLES: Record<BadgeType, { className: string; label: string }> = {
  electricity: { className: "bg-yellow-100 text-yellow-700", label: "电费" },
  water: { className: "bg-blue-100 text-blue-700", label: "水费" },
  gas: { className: "bg-green-100 text-green-700", label: "燃气费" },
  other: { className: "bg-gray-100 text-gray-700", label: "其他" },
};

export default function TypeBadge({ type }: TypeBadgeProps) {
  const meta = TYPE_STYLES[type];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        meta.className,
      )}
    >
      {meta.label}
    </span>
  );
}
