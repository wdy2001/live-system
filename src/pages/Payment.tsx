import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, X, CreditCard, Receipt } from "lucide-react";
import api from "@/lib/api";
import type { Bill, UtilityType } from "@/types";
import { UTILITY_META, UTILITY_LIST, formatMoney } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import TypeBadge from "@/components/TypeBadge";
import { SkeletonList } from "@/components/Skeleton";
import { cn } from "@/lib/utils";

export default function Payment() {
  const navigate = useNavigate();
  const [type, setType] = useState<UtilityType>("electricity");
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<Bill | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ transaction_no: string; amount: number } | null>(null);

  const load = (t: UtilityType) => {
    setLoading(true);
    api.get("/bills", { params: { type: t, status: "unpaid" } })
      .then((r) => setBills(r.data.bills))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(type); }, [type]);

  const handlePay = async () => {
    if (!paying) return;
    setSubmitting(true);
    try {
      const { data } = await api.post(`/bills/${paying.id}/pay`, { method: "alipay" });
      setResult({ transaction_no: data.transaction_no, amount: data.bill.amount });
      setPaying(null);
    } catch {
      /* 错误由拦截器处理 */
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title="缴费中心" subtitle="选择费用类型，一键完成在线缴费" />

      {/* 类型 Tab */}
      <div className="mb-6 flex gap-2">
        {UTILITY_LIST.map((t) => {
          const meta = UTILITY_META[t];
          const Icon = meta.icon;
          const active = type === t;
          return (
            <button
              key={t}
              onClick={() => setType(t)}
              className={cn(
                "flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-medium transition-all",
                active
                  ? `${meta.solid} text-white shadow-card`
                  : "bg-white text-ink-soft hover:bg-forest-50",
              )}
            >
              <Icon className="h-4 w-4" />
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* 账单列表 */}
      {loading ? (
        <SkeletonList count={3} />
      ) : bills.length === 0 ? (
        <div className="card flex flex-col items-center py-16 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-forest-50">
            <CheckCircle2 className="h-8 w-8 text-forest-500" />
          </div>
          <p className="font-medium text-ink">暂无待缴的{UTILITY_META[type].label}账单</p>
          <p className="mt-1 text-sm text-ink-muted">本月费用已结清，感谢及时缴费！</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bills.map((b, i) => {
            const meta = UTILITY_META[b.type];
            const Icon = meta.icon;
            return (
              <div
                key={b.id}
                className="card card-hover flex flex-wrap items-center gap-4 animate-fade-up"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <span className={cn("flex h-12 w-12 items-center justify-center rounded-xl", meta.bg, meta.text)}>
                  <Icon className="h-6 w-6" />
                </span>
                <div className="min-w-[140px] flex-1">
                  <div className="flex items-center gap-2">
                    <TypeBadge type={b.type} size="sm" />
                    <span className="text-sm font-medium text-ink">{b.period} 期</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-muted">
                    上期读数 {b.previous_reading} → 本期读数 {b.current_reading}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-ink-muted">用量</p>
                  <p className="font-medium text-ink">{b.usage_amount} {meta.unit}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-ink-muted">应缴金额</p>
                  <p className="font-serif text-xl font-bold text-energy-600">{formatMoney(b.amount)}</p>
                </div>
                <button onClick={() => setPaying(b)} className="btn-primary">
                  <CreditCard className="h-4 w-4" /> 立即缴费
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* 支付确认弹窗 */}
      {paying && (
        <Modal onClose={() => setPaying(null)}>
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-energy-50 text-energy-600">
              <Receipt className="h-7 w-7" />
            </div>
            <h3 className="font-serif text-xl font-bold text-forest-800">确认缴费</h3>
            <p className="mt-1 text-sm text-ink-muted">{paying.period} 期 {UTILITY_META[paying.type].label}</p>
          </div>
          <div className="my-6 space-y-2 rounded-xl bg-cream/70 p-4 text-sm">
            <Row label="费用类型" value={UTILITY_META[paying.type].label} />
            <Row label="计费周期" value={paying.period} />
            <Row label="用量" value={`${paying.usage_amount} ${UTILITY_META[paying.type].unit}`} />
            <Row label="读数变化" value={`${paying.previous_reading} → ${paying.current_reading}`} />
            <div className="my-2 border-t border-forest-100" />
            <div className="flex items-center justify-between">
              <span className="text-ink-muted">实付金额</span>
              <span className="font-serif text-2xl font-bold text-energy-600">{formatMoney(paying.amount)}</span>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setPaying(null)} className="btn-ghost flex-1 border border-forest-100">
              取消
            </button>
            <button onClick={handlePay} disabled={submitting} className="btn-primary flex-1">
              {submitting ? "支付中..." : "确认支付"}
            </button>
          </div>
          <p className="mt-3 text-center text-xs text-ink-muted">模拟支付 · 不会发生真实扣款</p>
        </Modal>
      )}

      {/* 支付成功弹窗 */}
      {result && (
        <Modal onClose={() => { setResult(null); load(type); }}>
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-forest-50">
              <CheckCircle2 className="h-9 w-9 text-forest-600" />
            </div>
            <h3 className="font-serif text-xl font-bold text-forest-800">缴费成功</h3>
            <p className="mt-1 text-sm text-ink-muted">感谢您及时缴费</p>
          </div>
          <div className="my-6 space-y-2 rounded-xl bg-cream/70 p-4 text-sm">
            <Row label="支付金额" value={formatMoney(result.amount)} />
            <Row label="交易单号" value={result.transaction_no} />
            <Row label="支付方式" value="模拟支付宝" />
          </div>
          <div className="flex gap-3">
            <button onClick={() => { setResult(null); load(type); }} className="btn-ghost flex-1 border border-forest-100">
              继续缴费
            </button>
            <button onClick={() => navigate("/records")} className="btn-primary flex-1">
              查看记录
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-ink-muted">{label}</span>
      <span className="font-medium text-ink">{value}</span>
    </div>
  );
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-forest-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md animate-scale-in rounded-2xl bg-cream p-6 shadow-cardHover">
        <button onClick={onClose} className="absolute right-4 top-4 rounded-lg p-1.5 text-ink-muted hover:bg-forest-50">
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  );
}
