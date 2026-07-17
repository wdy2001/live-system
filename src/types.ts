/** 公共类型定义 */

export type UtilityType = "electricity" | "water" | "gas";

export type BillStatus = "unpaid" | "paid";

export type RepairType = "electricity" | "water" | "gas" | "other";

export type RepairStatus = "pending" | "processing" | "resolved";

export interface User {
  id: number;
  username: string;
  real_name: string;
  phone: string;
  role: "user" | "admin";
  created_at: string;
}

export interface Meter {
  id: number;
  household_id: number;
  type: UtilityType;
  meter_no: string;
  current_reading: number;
}

export interface Household {
  id: number;
  household_no: string;
  address: string;
  user_id: number;
  meters?: Meter[];
}

export interface BillTypeRule {
  id: number;
  type: UtilityType;
  tier: number;
  min_usage: number;
  max_usage: number | null;
  unit_price: number;
  description: string;
}

export interface BillBreakdown {
  tier: number;
  min_usage: number;
  max_usage: number | null;
  unit_price: number;
  usage_in_tier: number;
  subtotal: number;
  description: string;
}

export interface Bill {
  id: number;
  household_id: number;
  meter_id: number;
  type: UtilityType;
  period: string;
  previous_reading: number;
  current_reading: number;
  usage_amount: number;
  amount: number;
  status: BillStatus;
  created_at: string;
  paid_at: string | null;
  breakdown?: BillBreakdown[];
  household?: Household;
  meter?: Meter;
  payment?: Payment;
}

export interface Payment {
  id: number;
  bill_id: number;
  amount: number;
  method: string;
  transaction_no: string;
  paid_at: string;
}

export interface RepairRequest {
  id: number;
  user_id: number;
  type: RepairType;
  description: string;
  phone: string;
  urgency: "normal" | "urgent";
  status: RepairStatus;
  created_at: string;
  resolved_at: string | null;
}

export interface Dashboard {
  unpaid_total: number;
  unpaid_count: number;
  this_month_usage: Record<UtilityType, number>;
  repair_stats: Record<"pending" | "processing" | "resolved", number>;
  trends: Array<{ period: string; usage: Record<UtilityType, number> }>;
  households: Household[];
}
