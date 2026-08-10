import { cn } from "@/lib/utils";

type SkeletonVariant = "line" | "card";

interface SkeletonProps {
  variant?: SkeletonVariant;
  className?: string;
}

export function Skeleton({ variant = "line", className }: SkeletonProps) {
  const baseStyles = "relative overflow-hidden bg-gray-200 animate-pulse";
  const variantStyles = variant === "card" ? "rounded-xl" : "rounded";

  return (
    <div className={cn(baseStyles, variantStyles, className)}>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
    </div>
  );
}

export function SkeletonLine({ className, count = 1 }: { className?: string; count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="line" className={cn("h-4 w-full", className)} />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return <Skeleton variant="card" className={cn("h-40 w-full", className)} />;
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="card" className="h-20 w-full" />
      ))}
    </div>
  );
}
