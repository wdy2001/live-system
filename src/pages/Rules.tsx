import { useEffect, useState } from "react";
import { Calculator, Zap, Droplets, Flame, Info } from "lucide-react";
import api from "@/lib/api";
import type { BillTypeRule, UtilityType } from "@/types";
import { UTILITY_META, UTILITY_LIST } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import { Skeleton } from "@/components/Skeleton";
import { cn } from "@/lib/utils";

export default function Rules() {
  const [rules, setRules] = useState<BillTypeRule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/rules")
      .then((r) => setRules(r.data.rules))
      .finally(() => setLoading(false));
  }, []);

  const byType = (t: UtilityType) => rules.filter((r) => r.type === t).sort((a, b) => a.tier - b.tier);

  return (
    <>
      <PageHeader
        title="计费规则"
        subtitle="阶梯定价标准公开透明，了解你家的费用如何计算"
      />

      {/* 信息提示 */}
      <div className="card mb-6 flex items-start gap-3 border border-aqua-100 bg-aqua-50/50">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-aqua-500" />
        <div className="text-sm text-ink-soft">
          <p className="font-medium text-aqua-700">什么是阶梯计价？</p>
          <p className="mt-1">
            阶梯计价按用量分档定价：用量越高、单价越高，鼓励节约能源。
            系统按各档用量分别计算后累加，得出账单总额。
          </p>
        </div>
      </div>

      {/* 三栏阶梯卡片 */}
      {loading ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-80" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {UTILITY_LIST.map((t, idx) => {
            const meta = UTILITY_META[t];
            const Icon = meta.icon;
            const typeRules = byType(t);
            return (
              <div
                key={t}
                className="card animate-fade-up overflow-hidden p-0"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                {/* 头部 */}
                <div className={cn("flex items-center gap-3 p-5", meta.bg)}>
                  <span className={cn("flex h-11 w-11 items-center justify-center rounded-xl bg-white/80", meta.text)}>
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-serif text-lg font-bold text-ink">{meta.label}阶梯价</h3>
                    <p className="text-xs text-ink-soft">计量单位：{meta.unit}</p>
                  </div>
                </div>

                {/* 阶梯列表 */}
                <div className="space-y-3 p-5">
                  {typeRules.map((r) => {
                    const range = r.max_usage === null
                      ? `${r.min_usage} ${meta.unit} 以上`
                      : `${r.min_usage} - ${r.max_usage} ${meta.unit}`;
                    return (
                      <div key={r.id} className="rounded-xl border border-forest-50 p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold text-white", meta.solid)}>
                              {r.tier}
                            </span>
                            <span className="text-sm font-medium text-ink">第 {r.tier} 档</span>
                          </div>
                          <span className="font-serif text-lg font-bold text-ink">
                            ¥{r.unit_price}
                            <span className="text-xs font-normal text-ink-muted">/{meta.unit}</span>
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-ink-muted">{range}</p>
                        {r.description && <p className="mt-0.5 text-xs text-ink-muted">{r.description}</p>}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 计算示例 */}
      <div className="card mt-6 animate-fade-up" style={{ animationDelay: "350ms" }}>
        <div className="mb-4 flex items-center gap-2">
          <Calculator className="h-5 w-5 text-forest-600" />
          <h3 className="font-serif text-lg font-bold text-forest-800">计算示例</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Example
            icon={Zap} meta={UTILITY_META.electricity}
            usage={250} unit="度"
            calc={[
              { tier: 1, range: "0-180 度", usage: 180, price: 0.588, subtotal: 105.84 },
              { tier: 2, range: "181-250 度", usage: 70, price: 0.638, subtotal: 44.66 },
            ]}
            total={150.5}
          />
          <Example
            icon={Droplets} meta={UTILITY_META.water}
            usage={15} unit="吨"
            calc={[
              { tier: 1, range: "0-12 吨", usage: 12, price: 3.5, subtotal: 42.0 },
              { tier: 2, range: "13-15 吨", usage: 3, price: 4.6, subtotal: 13.8 },
            ]}
            total={55.8}
          />
          <Example
            icon={Flame} meta={UTILITY_META.gas}
            usage={45} unit="立方"
            calc={[
              { tier: 1, range: "0-45 立方", usage: 45, price: 2.67, subtotal: 120.15 },
            ]}
            total={120.15}
          />
        </div>
      </div>
    </>
  );
}

function Example({
  icon: Icon, meta, usage, unit, calc, total,
}: {
  icon: typeof Zap;
  meta: typeof UTILITY_META.electricity;
  usage: number;
  unit: string;
  calc: Array<{ tier: number; range: string; usage: number; price: number; subtotal: number }>;
  total: number;
}) {
  return (
    <div className="rounded-2xl border border-forest-50 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className={cn("flex h-8 w-8 items-center justify-center rounded-lg", meta.bg, meta.text)}>
          <Icon className="h-4 w-4" />
        </span>
        <span className="text-sm font-medium text-ink">{meta.label} · 用 {usage} {unit}</span>
      </div>
      <div className="space-y-1.5 text-xs">
        {calc.map((c) => (
          <div key={c.tier} className="flex items-center justify-between text-ink-muted">
            <span>第{c.tier}档 {c.usage}{unit}×¥{c.price}</span>
            <span className="text-ink-soft">¥{c.subtotal}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between border-t border-forest-50 pt-2">
        <span className="text-sm text-ink-muted">合计</span>
        <span className="font-serif text-lg font-bold text-energy-600">¥{total.toFixed(2)}</span>
      </div>
    </div>
  );
}
