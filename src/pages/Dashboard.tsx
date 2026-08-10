import { useEffect, useState } from "react";
import { Wallet, BarChart3, Wrench, ReceiptText } from "lucide-react";
import api from "@/lib/api";
import type { DashboardResponse, Bill } from "@/types";
import { formatMoney } from "@/lib/utils";
import { STATUS_MAP } from "@/lib/constants";
import StatCard from "@/components/StatCard";
import UsageChart from "@/components/UsageChart";
import TypeBadge from "@/components/TypeBadge";
import { SkeletonCard, SkeletonList } from "@/components/Skeleton";
import { useAuthStore } from "@/store/auth";
import { PageHeader } from "@/components/Layout";

export default function Dashboard() {
  const { user } = useAuthStore();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardResponse>("/dashboard"),
      api.get<{ bills: Bill[] }>("/bills", { params: { per_page: 5 } }),
    ])
      .then(([dashboardRes, billsRes]) => {
        setData(dashboardRes.data);
        setBills(billsRes.data.bills || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const monthUsageValue = data
    ? `${data.this_month_usage.electricity.toFixed(1)}度 / ${data.this_month_usage.water.toFixed(1)}吨 / ${data.this_month_usage.gas.toFixed(1)}立方`
    : "0度 / 0吨 / 0立方";

  return (
    <>
      <PageHeader
        title={`你好，${user?.real_name ?? "居民"}`}
        subtitle="这里是你家的缴费概览与近期动态"
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <SkeletonCard className="h-32" />
          <SkeletonCard className="h-32" />
          <SkeletonCard className="h-32" />
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <StatCard
            icon={<Wallet className="h-6 w-6" />}
            title="待缴总额"
            value={formatMoney(data.unpaid_total)}
            subValue={`共 ${data.unpaid_count} 条待缴`}
            variant="orange"
          />
          <StatCard
            icon={<BarChart3 className="h-6 w-6" />}
            title="本月用量"
            value={monthUsageValue}
            subValue="本月用量合计"
            variant="blue"
          />
          <StatCard
            icon={<Wrench className="h-6 w-6" />}
            title="待处理报修"
            value={data.repair_stats.pending}
            subValue="待处理工单"
            variant="green"
          />
        </div>
      ) : null}

      <div className="mt-6 bg-white rounded-2xl shadow-sm p-6">
        <div className="mb-4">
          <h3 className="text-lg font-bold text-gray-800">近 6 月用量趋势</h3>
        </div>
        {loading ? (
          <SkeletonCard className="h-[300px]" />
        ) : data && data.trends && data.trends.length > 0 ? (
          <UsageChart data={data.trends} />
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
              <BarChart3 className="h-7 w-7 text-gray-400" />
            </div>
            <p className="text-sm text-gray-500">暂无用量数据</p>
          </div>
        )}
      </div>

      <div className="mt-6 bg-white rounded-2xl shadow-sm p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">最近账单</h3>
        </div>
        {loading ? (
          <SkeletonList count={5} />
        ) : bills.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {bills.map((bill) => {
              const statusMeta = STATUS_MAP[bill.status];
              return (
                <div
                  key={bill.id}
                  className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                >
                  <div className="flex items-center gap-3">
                    <TypeBadge type={bill.type} />
                    <span className="text-sm text-gray-600">{bill.period}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-bold text-gray-800">
                      {formatMoney(bill.amount)}
                    </span>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusMeta.color}`}
                    >
                      {statusMeta.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
              <ReceiptText className="h-7 w-7 text-gray-400" />
            </div>
            <p className="text-sm text-gray-500">暂无账单记录</p>
          </div>
        )}
      </div>
    </>
  );
}
