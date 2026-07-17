import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Wallet, ReceiptText, Gauge, Wrench, ArrowRight, Zap, Droplets, Flame,
} from "lucide-react";
import api from "@/lib/api";
import type { Dashboard as DashboardData, Bill } from "@/types";
import { UTILITY_META, UTILITY_LIST, formatMoney } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import StatCard from "@/components/StatCard";
import UsageChart from "@/components/UsageChart";
import TypeBadge from "@/components/TypeBadge";
import { Skeleton } from "@/components/Skeleton";
import { useAuthStore } from "@/store/auth";

export default function Dashboard() {
  const { user } = useAuthStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [unpaid, setUnpaid] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/dashboard"),
      api.get("/bills", { params: { status: "unpaid" } }),
    ])
      .then(([d, b]) => {
        setData(d.data);
        setUnpaid(b.data.bills);
      })
      .finally(() => setLoading(false));
  }, []);

  const monthUsage = data ? Object.values(data.this_month_usage).reduce((a, b) => a + b, 0) : 0;
  const repairActive = data ? data.repair_stats.pending + data.repair_stats.processing : 0;

  return (
    <>
      <PageHeader
        title={`你好，${user?.real_name ?? "居民"}`}
        subtitle="这里是你家的缴费概览与近期动态"
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="待缴总额" value={formatMoney(data?.unpaid_total ?? 0)} hint={`${data?.unpaid_count ?? 0} 笔待缴`} icon={Wallet} accent="energy" delay={0} />
          <StatCard label="本月用量" value={monthUsage.toFixed(1)} hint="电+水+气 合计" icon={Gauge} accent="forest" delay={80} />
          <StatCard label="已缴记录" value={`${(data?.trends.length ?? 0) * 3 - (data?.unpaid_count ?? 0)}`} hint="近 6 个月" icon={ReceiptText} accent="aqua" delay={160} />
          <StatCard label="报修处理中" value={`${repairActive}`} hint={`已完成 ${data?.repair_stats.resolved ?? 0} 单`} icon={Wrench} accent="clay" delay={240} />
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* 用量趋势 */}
        <div className="card lg:col-span-2 animate-fade-up" style={{ animationDelay: "300ms" }}>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-serif text-lg font-bold text-forest-800">近 6 月用量趋势</h3>
              <p className="text-xs text-ink-muted">电费 / 水费 / 燃气用量对比</p>
            </div>
          </div>
          {loading ? <Skeleton className="h-[280px] w-full" /> : <UsageChart data={data?.trends ?? []} />}
        </div>

        {/* 快捷缴费 */}
        <div className="card animate-fade-up" style={{ animationDelay: "380ms" }}>
          <h3 className="mb-4 font-serif text-lg font-bold text-forest-800">快捷缴费</h3>
          <div className="space-y-3">
            {UTILITY_LIST.map((t) => {
              const meta = UTILITY_META[t];
              const Icon = meta.icon;
              return (
                <Link
                  key={t}
                  to="/payment"
                  className="group flex items-center gap-3 rounded-xl border border-forest-50 p-3 transition hover:border-forest-200 hover:bg-forest-50/40"
                >
                  <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${meta.bg} ${meta.text}`}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-ink">{meta.label}</p>
                    <p className="text-xs text-ink-muted">前往缴费</p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-ink-muted transition group-hover:translate-x-1 group-hover:text-forest-600" />
                </Link>
              );
            })}
          </div>
          <Link to="/repair" className="btn-ghost mt-4 w-full border border-forest-100">
            <Wrench className="h-4 w-4" /> 提交故障报修
          </Link>
        </div>
      </div>

      {/* 待缴账单预览 */}
      <div className="card mt-6 animate-fade-up" style={{ animationDelay: "460ms" }}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-serif text-lg font-bold text-forest-800">待缴账单</h3>
          <Link to="/records" className="text-sm font-medium text-forest-600 hover:underline">
            查看全部
          </Link>
        </div>
        {loading ? (
          <Skeleton className="h-24 w-full" />
        ) : unpaid.length === 0 ? (
          <div className="flex flex-col items-center py-8 text-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-forest-50">
              <ReceiptText className="h-7 w-7 text-forest-500" />
            </div>
            <p className="text-sm text-ink-muted">暂无待缴账单，真棒！</p>
          </div>
        ) : (
          <div className="space-y-2">
            {unpaid.slice(0, 5).map((b) => {
              const meta = UTILITY_META[b.type];
              const Icon = meta.icon;
              return (
                <div key={b.id} className="flex items-center gap-3 rounded-xl bg-cream/60 px-4 py-3">
                  <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${meta.bg} ${meta.text}`}>
                    <Icon className="h-4 w-4" />
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <TypeBadge type={b.type} size="sm" />
                      <span className="text-xs text-ink-muted">{b.period}</span>
                    </div>
                    <p className="mt-0.5 text-xs text-ink-muted">
                      用量 {b.usage_amount} {meta.unit} · 读数 {b.previous_reading} → {b.current_reading}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-serif font-bold text-energy-600">{formatMoney(b.amount)}</p>
                  </div>
                  <Link to="/payment" className="btn-primary px-3 py-1.5 text-xs">
                    缴费
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );
}
