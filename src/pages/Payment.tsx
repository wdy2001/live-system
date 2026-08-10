import { useEffect, useState } from "react";
import { X, Loader2 } from "lucide-react";
import api from "@/lib/api";
import type { Bill, UtilityType } from "@/types";
import { formatMoney } from "@/lib/utils";
import { PageHeader } from "@/components/Layout";
import TypeBadge from "@/components/TypeBadge";
import { SkeletonList } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { cn } from "@/lib/utils";

type FilterType = UtilityType | "";

const TABS: Array<{ key: FilterType; label: string }> = [
  { key: "", label: "全部" },
  { key: "electricity", label: "电费" },
  { key: "water", label: "水费" },
  { key: "gas", label: "燃气费" },
];

const UNIT_MAP: Record<UtilityType, string> = {
  electricity: "度",
  water: "吨",
  gas: "立方",
};

export default function Payment() {
  const { showToast } = useToast();
  const [filterType, setFilterType] = useState<FilterType>("");
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<Bill | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [payMethod, setPayMethod] = useState<"alipay" | "wechat">("alipay");

  const loadBills = (t: FilterType) => {
    setLoading(true);
    const params: Record<string, string> = { status: "unpaid" };
    if (t) params.type = t;
    api
      .get("/bills", { params })
      .then((r) => setBills(r.data.bills || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadBills(filterType);
  }, [filterType]);

  const openPayModal = (bill: Bill) => {
    setPaying(bill);
    setPayMethod("alipay");
  };

  const handleConfirmPay = async () => {
    if (!paying || submitting) return;
    setSubmitting(true);
    try {
      const { data } = await api.post(`/bills/${paying.id}/pay`, { method: payMethod });
      const transactionNo = data?.payment?.transaction_no || data?.transaction_no || "";
      showToast(`支付成功！交易号: ${transactionNo}`, "success");
      setTimeout(() => {
        setPaying(null);
        loadBills(filterType);
      }, 1000);
    } catch (err: any) {
      const msg = err?.message || "支付失败，请稍后重试";
      showToast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title="缴费中心" subtitle="选择费用类型，一键完成在线缴费" />

      {/* Tab 导航 */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-8">
          {TABS.map((tab) => {
            const active = filterType === tab.key;
            return (
              <button
                key={tab.key || "all"}
                onClick={() => setFilterType(tab.key)}
                className={cn(
                  "relative pb-3 text-sm transition-colors",
                  active
                    ? "font-bold text-blue-600"
                    : "font-medium text-gray-500 hover:text-gray-700"
                )}
              >
                {tab.label}
                {active && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 账单列表 */}
      {loading ? (
        <SkeletonList count={3} />
      ) : bills.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm flex flex-col items-center py-16 text-center">
          <p className="font-medium text-gray-800">暂无待缴账单</p>
          <p className="mt-1 text-sm text-gray-500">本月费用已结清，感谢及时缴费！</p>
        </div>
      ) : (
        <div>
          {bills.map((bill) => {
            const unit = UNIT_MAP[bill.type];
            const householdNo = bill.household?.household_no || "-";
            const meterNo = bill.meter?.meter_no || "-";
            return (
              <div
                key={bill.id}
                className="bg-white rounded-xl shadow-sm p-5 mb-4 grid grid-cols-1 md:grid-cols-12 gap-4 items-center"
              >
                {/* 左侧 */}
                <div className="md:col-span-4">
                  <div className="flex items-center gap-2 mb-2">
                    <TypeBadge type={bill.type} />
                  </div>
                  <p className="text-xl font-bold text-gray-800">{bill.period}</p>
                  <p className="text-sm text-gray-500 mt-1">户号 {householdNo}</p>
                </div>

                {/* 中间 */}
                <div className="md:col-span-4">
                  <p className="text-lg font-semibold text-gray-800">
                    {bill.usage_amount}
                    <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
                  </p>
                  <p className="text-sm text-gray-500 mt-1">表号 {meterNo}</p>
                </div>

                {/* 右侧 */}
                <div className="md:col-span-4 flex items-center justify-between md:justify-end gap-4">
                  <div className="text-right">
                    <p className="text-2xl font-bold text-gray-800">
                      {formatMoney(bill.amount)}
                    </p>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-600 mt-1">
                      待缴费
                    </span>
                  </div>
                  <button
                    onClick={() => openPayModal(bill)}
                    className="bg-blue-500 hover:bg-blue-600 text-white rounded-lg px-5 py-2 font-medium transition-colors whitespace-nowrap"
                  >
                    去支付
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 支付确认弹窗 */}
      {paying && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-gray-900/40 backdrop-blur-sm"
            onClick={() => !submitting && setPaying(null)}
          />
          <div className="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl animate-scale-in">
            <button
              onClick={() => !submitting && setPaying(null)}
              disabled={submitting}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 disabled:opacity-50"
            >
              <X className="h-4 w-4" />
            </button>

            <h3 className="text-xl font-bold text-gray-800 text-center mb-5">确认支付</h3>

            {/* 账单摘要 */}
            <div className="bg-gray-50 rounded-xl p-4 mb-5 space-y-3">
              <div className="flex items-center gap-2">
                <TypeBadge type={paying.type} />
                <span className="text-sm font-medium text-gray-700">
                  {paying.period} 期
                </span>
              </div>
              <div className="text-sm text-gray-600">
                户号：{paying.household?.household_no || "-"}
              </div>
              <div className="pt-3 border-t border-gray-200">
                <p className="text-sm text-gray-500 mb-1">应付金额</p>
                <p className="text-3xl font-bold text-gray-800">
                  {formatMoney(paying.amount)}
                </p>
              </div>
            </div>

            {/* 支付方式 */}
            <div className="mb-6">
              <p className="text-sm font-medium text-gray-700 mb-3">选择支付方式</p>
              <div className="grid grid-cols-2 gap-3">
                <label
                  className={cn(
                    "flex items-center justify-center gap-2 border-2 rounded-xl py-3 cursor-pointer transition-all",
                    payMethod === "alipay"
                      ? "border-blue-500 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  )}
                >
                  <input
                    type="radio"
                    name="payMethod"
                    value="alipay"
                    checked={payMethod === "alipay"}
                    onChange={() => setPayMethod("alipay")}
                    className="sr-only"
                  />
                  <span className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                    style={{ borderColor: payMethod === "alipay" ? "#3b82f6" : "#d1d5db" }}
                  >
                    {payMethod === "alipay" && <span className="w-2 h-2 rounded-full bg-blue-500" />}
                  </span>
                  <span className="font-medium">支付宝</span>
                </label>
                <label
                  className={cn(
                    "flex items-center justify-center gap-2 border-2 rounded-xl py-3 cursor-pointer transition-all",
                    payMethod === "wechat"
                      ? "border-green-500 bg-green-50 text-green-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  )}
                >
                  <input
                    type="radio"
                    name="payMethod"
                    value="wechat"
                    checked={payMethod === "wechat"}
                    onChange={() => setPayMethod("wechat")}
                    className="sr-only"
                  />
                  <span className="w-4 h-4 rounded-full border-2 flex items-center justify-center"
                    style={{ borderColor: payMethod === "wechat" ? "#22c55e" : "#d1d5db" }}
                  >
                    {payMethod === "wechat" && <span className="w-2 h-2 rounded-full bg-green-500" />}
                  </span>
                  <span className="font-medium">微信</span>
                </label>
              </div>
            </div>

            {/* 底部按钮 */}
            <div className="flex gap-3">
              <button
                onClick={() => setPaying(null)}
                disabled={submitting}
                className="flex-1 rounded-lg border border-gray-200 py-2.5 font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleConfirmPay}
                disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white py-2.5 font-medium disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    支付中...
                  </>
                ) : (
                  "确认支付"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
