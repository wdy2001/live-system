import { useEffect, useState } from "react";
import { X, ReceiptText, TrendingUp } from "lucide-react";
import api from "@/lib/api";
import type { Bill, UtilityType, BillStatus } from "@/types";
import { UTILITY_META, UTILITY_LIST, BILL_STATUS_META, formatMoney } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import TypeBadge from "@/components/TypeBadge";
import { SkeletonList } from "@/components/Skeleton";
import { cn } from "@/lib/utils";

type Filter = "all" | UtilityType;
type StatusFilter = "all" | BillStatus;

export default function Records() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [detail, setDetail] = useState<Bill | null>(null);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (filter !== "all") params.type = filter;
    if (status !== "all") params.status = status;
    api.get("/bills", { params })
      .then((r) => setBills(r.data.bills))
      .finally(() => setLoading(false));
  }, [filter, status]);

  const openDetail = (id: number) => {
    api.get(`/bills/${id}`).then((r) => setDetail(r.data.bill));
  };

  // 统计
  const paidTotal = bills.filter((b) => b.status === "paid").reduce((s, b) => s + b.amount, 0);
  const unpaidTotal = bills.filter((b) => b.status === "unpaid").reduce((s, b) => s + b.amount, 0);

  return (
    <>
      <PageHeader title="缴费记录" subtitle="按费用类型与状态分类查看历史账单" />

      {/* 统计条 */}
      <div className="mb-6 grid grid-cols-2 gap-4">
        <div className="card flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-forest-50 text-forest-600">
            <ReceiptText className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-ink-muted">已缴总额</p>
            <p className="font-serif text-lg font-bold text-forest-700">{formatMoney(paidTotal)}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-energy-50 text-energy-600">
            <TrendingUp className="h-5 w-5" />
          </span>
          <div>
            <p className="text-xs text-ink-muted">待缴总额</p>
            <p className="font-serif text-lg font-bold text-energy-600">{formatMoney(unpaidTotal)}</p>
          </div>
        </div>
      </div>

      {/* 筛选 */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="mr-1 text-sm text-ink-muted">类型</span>
        <Chip active={filter === "all"} onClick={() => setFilter("all")}>全部</Chip>
        {UTILITY_LIST.map((t) => (
          <Chip key={t} active={filter === t} onClick={() => setFilter(t)}>
            {UTILITY_META[t].label}
          </Chip>
        ))}
        <span className="mx-2 text-sm text-ink-muted">状态</span>
        <Chip active={status === "all"} onClick={() => setStatus("all")}>全部</Chip>
        <Chip active={status === "unpaid"} onClick={() => setStatus("unpaid")}>待缴费</Chip>
        <Chip active={status === "paid"} onClick={() => setStatus("paid")}>已缴费</Chip>
      </div>

      {/* 列表 */}
      {loading ? (
        <SkeletonList count={5} />
      ) : bills.length === 0 ? (
        <div className="card flex flex-col items-center py-16 text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-forest-50">
            <ReceiptText className="h-7 w-7 text-forest-500" />
          </div>
          <p className="text-sm text-ink-muted">没有符合条件的账单记录</p>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          {/* 表头 */}
          <div className="hidden grid-cols-12 gap-3 border-b border-forest-50 bg-cream/50 px-5 py-3 text-xs font-medium text-ink-muted sm:grid">
            <span className="col-span-2">费用类型</span>
            <span className="col-span-2">计费周期</span>
            <span className="col-span-2">用量</span>
            <span className="col-span-2">金额</span>
            <span className="col-span-2">状态</span>
            <span className="col-span-2 text-right">操作</span>
          </div>
          <div className="divide-y divide-forest-50">
            {bills.map((b) => {
              const meta = UTILITY_META[b.type];
              return (
                <div
                  key={b.id}
                  className="grid grid-cols-2 items-center gap-3 px-5 py-4 transition hover:bg-cream/40 sm:grid-cols-12"
                >
                  <div className="col-span-2 sm:col-span-2">
                    <TypeBadge type={b.type} size="sm" />
                  </div>
                  <div className="col-span-1 text-sm text-ink sm:col-span-2">{b.period}</div>
                  <div className="col-span-1 text-sm text-ink-soft sm:col-span-2">
                    {b.usage_amount} {meta.unit}
                  </div>
                  <div className="col-span-1 font-serif font-bold text-ink sm:col-span-2">{formatMoney(b.amount)}</div>
                  <div className="col-span-1 sm:col-span-2">
                    <span className={cn("chip", BILL_STATUS_META[b.status].className)}>
                      {BILL_STATUS_META[b.status].label}
                    </span>
                  </div>
                  <div className="col-span-2 text-right sm:col-span-2">
                    <button onClick={() => openDetail(b.id)} className="btn-ghost px-3 py-1.5 text-xs">
                      详情
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 详情抽屉 */}
      {detail && <DetailDrawer bill={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-sm font-medium transition",
        active ? "bg-forest-700 text-white" : "bg-white text-ink-soft hover:bg-forest-50",
      )}
    >
      {children}
    </button>
  );
}

function DetailDrawer({ bill, onClose }: { bill: Bill; onClose: () => void }) {
  const meta = UTILITY_META[bill.type];
  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-forest-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative h-full w-full max-w-md animate-fade-up overflow-y-auto bg-cream p-6 shadow-cardHover">
        <button onClick={onClose} className="absolute right-4 top-4 rounded-lg p-1.5 text-ink-muted hover:bg-forest-50">
          <X className="h-4 w-4" />
        </button>

        <div className="mb-6">
          <TypeBadge type={bill.type} />
          <h3 className="mt-3 font-serif text-xl font-bold text-forest-800">{bill.period} 期账单明细</h3>
          <p className="mt-1 text-sm text-ink-muted">户号 {bill.household?.household_no} · {bill.household?.address}</p>
        </div>

        {/* 读数信息 */}
        <div className="card mb-4 bg-white">
          <h4 className="mb-3 text-sm font-medium text-ink-soft">表计读数</h4>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-xl bg-cream/60 p-3">
              <p className="text-xs text-ink-muted">上期读数</p>
              <p className="mt-1 font-serif text-lg font-bold text-ink">{bill.previous_reading}</p>
            </div>
            <div className="rounded-xl bg-cream/60 p-3">
              <p className="text-xs text-ink-muted">本期读数</p>
              <p className="mt-1 font-serif text-lg font-bold text-ink">{bill.current_reading}</p>
            </div>
            <div className="rounded-xl bg-forest-50 p-3">
              <p className="text-xs text-ink-muted">用量</p>
              <p className="mt-1 font-serif text-lg font-bold text-forest-700">{bill.usage_amount}</p>
            </div>
          </div>
          <p className="mt-2 text-center text-xs text-ink-muted">表号 {bill.meter?.meter_no} · 计量单位 {meta.unit}</p>
        </div>

        {/* 阶梯拆分 */}
        {bill.breakdown && bill.breakdown.length > 0 && (
          <div className="card mb-4 bg-white">
            <h4 className="mb-3 text-sm font-medium text-ink-soft">阶梯计费拆分</h4>
            <div className="space-y-2">
              {bill.breakdown.map((bd) => (
                <div key={bd.tier} className="rounded-xl border border-forest-50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-ink">第 {bd.tier} 档</span>
                    <span className="font-serif font-bold text-forest-700">{formatMoney(bd.subtotal)}</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-muted">
                    {bd.usage_in_tier} {meta.unit} × ¥{bd.unit_price}/{meta.unit}
                  </p>
                  {bd.description && <p className="mt-0.5 text-xs text-ink-muted">{bd.description}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 支付信息 */}
        <div className="card bg-white">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-muted">账单状态</span>
            <span className={cn("chip", BILL_STATUS_META[bill.status].className)}>
              {BILL_STATUS_META[bill.status].label}
            </span>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-forest-50 pt-3">
            <span className="text-sm text-ink-muted">应缴金额</span>
            <span className="font-serif text-2xl font-bold text-energy-600">{formatMoney(bill.amount)}</span>
          </div>
          {bill.payment && (
            <div className="mt-3 space-y-1 border-t border-forest-50 pt-3 text-xs text-ink-muted">
              <p>交易单号：{bill.payment.transaction_no}</p>
              <p>支付时间：{new Date(bill.payment.paid_at).toLocaleString("zh-CN")}</p>
              <p>支付方式：{bill.payment.method}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
