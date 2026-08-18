import { useEffect, useState, useMemo } from "react";
import { Info } from "lucide-react";
import api from "@/lib/api";
import type { BillTypeRule, UtilityType, BillBreakdown } from "@/types";
import type { RulesResponse } from "@/types";
import { UTILITY_META, UTILITY_LIST } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import { Skeleton } from "@/components/Skeleton";
import { cn } from "@/lib/utils";

const TIER_LABELS = ["第一档", "第二档", "第三档", "第四档", "第五档"];

const TAB_CONFIG: Array<{ type: UtilityType; label: string }> = [
  { type: "electricity", label: "电费" },
  { type: "water", label: "水费" },
  { type: "gas", label: "燃气费" },
];

function formatUnitPrice(price: number): string {
  const fixed4 = price.toFixed(4);
  if (fixed4.endsWith("00")) {
    return price.toFixed(2);
  }
  return fixed4;
}

export default function Rules() {
  const [currentType, setCurrentType] = useState<UtilityType>("electricity");
  const [rules, setRules] = useState<BillTypeRule[]>([]);
  const [example, setExample] = useState<RulesResponse["example"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [inputUsage, setInputUsage] = useState<number>(0);

  useEffect(() => {
    setLoading(true);
    api.get<RulesResponse>(`/rules?type=${currentType}`)
      .then((r) => {
        setRules(r.data.rules);
        setExample(r.data.example);
        setInputUsage(r.data.example.usage);
      })
      .finally(() => setLoading(false));
  }, [currentType]);

  const meta = UTILITY_META[currentType];

  const customCalc = useMemo(() => {
    if (!rules.length || inputUsage < 0) return { breakdown: [] as BillBreakdown[], total: 0 };
    let remaining = inputUsage;
    let total = 0;
    const breakdown: BillBreakdown[] = [];

    for (const rule of rules) {
      const tierMin = rule.min_usage;
      const tierMax = rule.max_usage;
      const tierCapacity = tierMax !== null ? tierMax - tierMin : remaining;
      let usedInTier = 0;
      if (remaining > 0) {
        usedInTier = Math.min(remaining, tierCapacity);
        if (usedInTier < 0) usedInTier = 0;
      }
      const subtotal = usedInTier * rule.unit_price;
      total += subtotal;
      remaining -= usedInTier;
      breakdown.push({
        tier: rule.tier,
        min_usage: tierMin,
        max_usage: tierMax,
        unit_price: rule.unit_price,
        usage_in_tier: usedInTier,
        subtotal: Number(subtotal.toFixed(2)),
        description: rule.description,
      });
    }

    return { breakdown, total: Number(total.toFixed(2)) };
  }, [rules, inputUsage]);

  const activeBreakdown = example && inputUsage === example.usage
    ? example.breakdown
    : customCalc.breakdown;
  const activeTotal = example && inputUsage === example.usage
    ? example.amount
    : customCalc.total;

  return (
    <>
      <PageHeader
        title="计费规则"
        subtitle="阶梯定价标准公开透明，了解你家的费用如何计算"
      />

      <div className="card mb-6 flex items-start gap-3 border border-blue-100 bg-blue-50/50">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-blue-500" />
        <div className="text-sm text-gray-600">
          <p className="font-medium text-blue-700">什么是阶梯计价？</p>
          <p className="mt-1">
            阶梯计价按用量分档定价：用量越高、单价越高，鼓励节约能源。
            系统按各档用量分别计算后累加，得出账单总额。
          </p>
        </div>
      </div>

      <div className="mb-6 flex gap-2 border-b border-gray-200">
        {TAB_CONFIG.map((tab) => {
          const isActive = tab.type === currentType;
          return (
            <button
              key={tab.type}
              onClick={() => setCurrentType(tab.type)}
              className={cn(
                "relative px-6 py-3 text-sm transition-all",
                isActive
                  ? "font-bold text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              )}
            >
              {tab.label}
              {isActive && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
              )}
            </button>
          );
        })}
      </div>

      {loading ? (
        <Skeleton className="h-80 w-full" />
      ) : (
        <>
          <div className="w-full rounded-xl bg-white shadow-sm">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50 text-left text-sm">
                  <th className="px-6 py-4 font-semibold text-gray-700">档位</th>
                  <th className="px-6 py-4 font-semibold text-gray-700">用量范围</th>
                  <th className="px-6 py-4 font-semibold text-gray-700">单价(元)</th>
                  <th className="px-6 py-4 font-semibold text-gray-700">说明</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => {
                  const rangeText = rule.max_usage === null
                    ? `${rule.min_usage} - ∞ ${meta.unit}`
                    : `${rule.min_usage} - ${rule.max_usage} ${meta.unit}`;
                  const tierLabel = TIER_LABELS[rule.tier - 1] || `第${rule.tier}档`;
                  return (
                    <tr key={rule.id} className="border-b border-gray-100 last:border-b-0">
                      <td className="px-6 py-4 text-sm font-medium text-gray-800">
                        {tierLabel}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {rangeText}
                      </td>
                      <td className="px-6 py-4 text-sm font-semibold text-gray-800">
                        ¥{formatUnitPrice(rule.unit_price)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {rule.description}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-8 rounded-xl border-2 border-blue-50 bg-white p-6 shadow-sm">
            <h3 className="text-lg font-bold text-gray-800">计算示例 💡</h3>
            <div className="mt-6 grid grid-cols-2 gap-6">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-600">
                  示例用量
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min={0}
                    value={inputUsage}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setInputUsage(isNaN(v) ? 0 : v);
                    }}
                    className="w-full rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />
                  <span className="text-sm text-gray-500">{meta.unit}</span>
                </div>
              </div>

              <div>
                <div className="space-y-2">
                  {activeBreakdown.map((b) => {
                    const tierLabel = TIER_LABELS[b.tier - 1] || `第${b.tier}档`;
                    return (
                      <div key={b.tier} className="text-sm text-gray-600">
                        {tierLabel}: {b.usage_in_tier} {meta.unit} × {formatUnitPrice(b.unit_price)} 元 = ¥{b.subtotal.toFixed(2)}
                      </div>
                    );
                  })}
                </div>
                <div className="my-4 h-px bg-gray-200" />
                <div className="text-xl font-bold text-gray-800">
                  合计: ¥{activeTotal.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
