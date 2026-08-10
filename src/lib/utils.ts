import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { TYPE_OPTIONS } from "@/lib/constants";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatMoney(n: number): string {
  return `¥${Number(n || 0).toFixed(2)}`;
}

export function formatDate(dateStr: string, withTime: boolean = true): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  if (!withTime) {
    return `${year}-${month}-${day}`;
  }
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

export function typeLabel(type: string): string {
  const key = type as keyof typeof TYPE_OPTIONS;
  return TYPE_OPTIONS[key]?.label || type;
}
