import {
  Zap, Droplets, Flame, type LucideIcon,
} from "lucide-react";
import type { UtilityType, RepairType, RepairStatus, BillStatus } from "@/types";

/** 缴费类型元信息：标签 / 颜色 / 图标 / 单位 */
export const UTILITY_META: Record<
  UtilityType,
  { label: string; icon: LucideIcon; unit: string; text: string; bg: string; ring: string; dot: string; solid: string }
> = {
  electricity: {
    label: "电费",
    icon: Zap,
    unit: "度",
    text: "text-energy-600",
    bg: "bg-energy-50",
    ring: "ring-energy-100",
    dot: "bg-energy-500",
    solid: "bg-energy-500",
  },
  water: {
    label: "水费",
    icon: Droplets,
    unit: "吨",
    text: "text-aqua-500",
    bg: "bg-aqua-50",
    ring: "ring-aqua-100",
    dot: "bg-aqua-500",
    solid: "bg-aqua-500",
  },
  gas: {
    label: "燃气费",
    icon: Flame,
    unit: "立方",
    text: "text-clay-500",
    bg: "bg-clay-50",
    ring: "ring-clay-100",
    dot: "bg-clay-500",
    solid: "bg-clay-500",
  },
};

export const UTILITY_LIST: UtilityType[] = ["electricity", "water", "gas"];

export const REPAIR_TYPE_LABEL: Record<RepairType, string> = {
  electricity: "电费故障",
  water: "水费故障",
  gas: "燃气故障",
  other: "其他故障",
};

export const BILL_STATUS_META: Record<BillStatus, { label: string; className: string }> = {
  unpaid: { label: "待缴费", className: "bg-energy-50 text-energy-600" },
  paid: { label: "已缴费", className: "bg-forest-50 text-forest-600" },
};

export const REPAIR_STATUS_META: Record<
  RepairStatus,
  { label: string; className: string; step: number }
> = {
  pending: { label: "待受理", className: "bg-clay-50 text-clay-500", step: 1 },
  processing: { label: "处理中", className: "bg-energy-50 text-energy-600", step: 2 },
  resolved: { label: "已完成", className: "bg-forest-50 text-forest-600", step: 3 },
};

export function formatMoney(n: number): string {
  return `¥${n.toFixed(2)}`;
}
