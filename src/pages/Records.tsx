import { useEffect, useState, useCallback } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import type { Bill, UtilityType, BillStatus } from "@/types";
import { UTILITY_META, formatMoney } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import TypeBadge from "@/components/TypeBadge";
import { cn, formatDate } from "@/lib/utils";

type Filter = "all" | UtilityType;
type StatusFilter = "all" | BillStatus;

interface BillsResponse {
  bills: Bill[];
  total: number;
  page: number;
  per_page: number;
}

const TYPE_OPTIONS: { value: Filter; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "electricity", label: "电费" },
  { value: "water", label: "水费" },
  { value: "gas", label: "燃气费" },
];

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "unpaid", label: "待缴" },
  { value: "paid", label: "已缴" },
];

export default function Records() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const perPage = 10;

  const [pendingFilter, setPendingFilter] = useState<Filter>("all");
  const [pendingStatus, setPendingStatus] = useState<StatusFilter>("all");
  const [appliedFilter, setAppliedFilter] = useState<Filter>("all");
  const [appliedStatus, setAppliedStatus] = useState<StatusFilter>("all");

  const [detail, setDetail] = useState<Bill | null>(null);

  const fetchBills = useCallback(
    (p: number, typeFilter: Filter, statusFilter: StatusFilter) => {
      setLoading(true);
      const params: Record<string, string | number> = {
        page: p,
        per_page: perPage,
      };
      if (typeFilter !== "all") params.type = typeFilter;
      if (statusFilter !== "all") params.status = statusFilter;
      api
        .get<BillsResponse>("/bills", { params })
        .then((r) => {
          setBills(r.data.bills);
          setTotal(r.data.total);
          setPage(r.data.page);
        })
        .finally(() => setLoading(false));
    },
    [],
  );

  useEffect(() => {
    fetchBills(1, appliedFilter, appliedStatus);
  }, [appliedFilter, appliedStatus, fetchBills]);

  const handleSearch = () => {
    setAppliedFilter(pendingFilter);
    setAppliedStatus(pendingStatus);
  };

  const handlePrevPage = () => {
    if (page > 1) {
      const newPage = page - 1;
      setPage(newPage);
      fetchBills(newPage, appliedFilter, appliedStatus);
    }
  };

  const handleNextPage = () => {
    const totalPages = Math.ceil(total / perPage);
    if (page < totalPages) {
      const newPage = page + 1;
      setPage(newPage);
      fetchBills(newPage, appliedFilter, appliedStatus);
    }
  };

  const openDetail = (id: number) => {
    api.get<{ bill: Bill }>(`/bills/${id}`).then((r) => setDetail(r.data.bill));
  };

  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const isFirstPage = page <= 1;
  const isLastPage = page >= totalPages;

  return (
    <>
      <PageHeader title="缴费记录" subtitle="按费用类型与状态分类查看历史账单" />

      {/* 筛选区 */}
      <div className="card mb-6">
        <div className="grid grid-cols-2 gap-4 items-end">
          <div>
            <label className="label">类型</label>
            <select
              className="input"
              value={pendingFilter}
              onChange={(e) => setPendingFilter(e.target.value as Filter)}
            >
              {TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col items-end">
            <label className="label w-full">状态</label>
            <div className="flex gap-3 w-full items-center">
              <select
                className="input flex-1"
                value={pendingStatus}
                onChange={(e) => setPendingStatus(e.target.value as StatusFilter)}
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <button
                onClick={handleSearch}
                className="btn bg-blue-500 text-white hover:bg-blue-600"
                style={{ whiteSpace: "nowrap" }}
              >
                搜索
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 表格 */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full table border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">周期</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">类型</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">用量</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">金额</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">状态</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="px-5 py-4">
                    <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-5 py-4">
                    <div className="h-5 w-12 bg-gray-200 rounded-full animate-pulse" />
                  </td>
                  <td className="px-5 py-4">
                    <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-5 py-4">
                    <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                  </td>
                  <td className="px-5 py-4">
                    <div className="h-5 w-12 bg-gray-200 rounded-full animate-pulse" />
                  </td>
                  <td className="px-5 py-4">
                    <div className="h-7 w-14 bg-gray-200 rounded-lg animate-pulse" />
                  </td>
                </tr>
              ))
            ) : bills.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-16 text-center text-sm text-gray-500">
                  没有符合条件的账单记录
                </td>
              </tr>
            ) : (
              bills.map((b) => {
                const meta = UTILITY_META[b.type];
                return (
                  <tr key={b.id} className="border-b border-gray-100 hover:bg-gray-50 transition">
                    <td className="px-5 py-4 text-sm text-gray-800">{b.period}</td>
                    <td className="px-5 py-4">
                      <TypeBadge type={b.type} />
                    </td>
                    <td className="px-5 py-4 text-sm text-gray-600">
                      {b.usage_amount} {meta.unit}
                    </td>
                    <td className="px-5 py-4 text-sm font-bold text-gray-800">{formatMoney(b.amount)}</td>
                    <td className="px-5 py-4">
                      <StatusBadge status={b.status} />
                    </td>
                    <td className="px-5 py-4">
                      <button
                        onClick={() => openDetail(b.id)}
                        className="text-blue-500 hover:text-blue-600 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-blue-50 transition"
                      >
                        详情
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 分页器 */}
      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          共 <span className="font-semibold text-gray-800">{total}</span> 条 / 每页 {perPage} 条
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            disabled={isFirstPage}
            className={cn(
              "btn px-3 py-2 gap-1",
              isFirstPage
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50",
            )}
          >
            <ChevronLeft className="h-4 w-4" />
            上一页
          </button>
          <span className="px-4 py-2 text-sm text-gray-700">
            第 <span className="font-semibold text-gray-900">{page}</span> / {totalPages} 页
          </span>
          <button
            onClick={handleNextPage}
            disabled={isLastPage}
            className={cn(
              "btn px-3 py-2 gap-1",
              isLastPage
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50",
            )}
          >
            下一页
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 详情弹窗 */}
      {detail && <DetailModal bill={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

function StatusBadge({ status }: { status: BillStatus }) {
  if (status === "unpaid") {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
        待缴
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
      已缴
    </span>
  );
}

function DetailModal({ bill, onClose }: { bill: Bill; onClose: () => void }) {
  const meta = UTILITY_META[bill.type];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-[600px] max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-xl animate-fade-up">
        {/* 标题栏 */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h3 className="text-lg font-bold text-gray-800">账单详情</h3>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {/* 基本信息栅格 */}
          <div className="grid grid-cols-2 gap-3">
            <InfoItem label="户号" value={bill.household?.household_no ?? "-"} />
            <InfoItem label="表号" value={bill.meter?.meter_no ?? "-"} />
            <InfoItem
              label="类型"
              value={
                <div className="inline-flex">
                  <TypeBadge type={bill.type} />
                </div>
              }
            />
            <InfoItem label="账单周期" value={bill.period} />
            <InfoItem label="上期读数" value={String(bill.previous_reading)} />
            <InfoItem label="本期读数" value={String(bill.current_reading)} />
            <InfoItem
              label="用量"
              value={`${bill.usage_amount} ${meta.unit}`}
            />
            <InfoItem
              label="缴费状态"
              value={
                <div className="inline-flex">
                  <StatusBadge status={bill.status} />
                </div>
              }
            />
            <InfoItem
              label="应付金额"
              value={<span className="font-bold text-gray-900">{formatMoney(bill.amount)}</span>}
            />
            <InfoItem
              label="缴费时间"
              value={bill.paid_at ? formatDate(bill.paid_at) : "-"}
            />
          </div>

          {/* 阶梯拆分表格 */}
          <div className="mt-6">
            <h4 className="text-sm font-semibold text-gray-800 mb-3">阶梯计费拆分</h4>
            <table className="w-full table border-collapse border border-gray-200 rounded-lg overflow-hidden">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-600 border-r border-gray-200">
                    档位
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-600 border-r border-gray-200">
                    用量范围
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-600 border-r border-gray-200">
                    本档用量
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-600 border-r border-gray-200">
                    单价(¥)
                  </th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-600">
                    小计(¥)
                  </th>
                </tr>
              </thead>
              <tbody>
                {bill.breakdown && bill.breakdown.length > 0 ? (
                  bill.breakdown.map((bd, idx) => {
                    const maxStr = bd.max_usage === null ? "∞" : String(bd.max_usage);
                    return (
                      <tr
                        key={bd.tier}
                        className={idx !== bill.breakdown!.length - 1 ? "border-b border-gray-200" : ""}
                      >
                        <td className="px-4 py-2.5 text-sm text-gray-700 border-r border-gray-200">
                          第{bd.tier}档
                        </td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 border-r border-gray-200">
                          {bd.min_usage}~{maxStr}
                        </td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 border-r border-gray-200">
                          {bd.usage_in_tier} {meta.unit}
                        </td>
                        <td className="px-4 py-2.5 text-sm text-gray-700 border-r border-gray-200">
                          {formatUnitPrice(bd.unit_price)}
                        </td>
                        <td className="px-4 py-2.5 text-sm text-gray-700">
                          {formatMoney(bd.subtotal)}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-500">
                      无阶梯拆分信息
                    </td>
                  </tr>
                )}
                {/* 合计行 */}
                <tr className="bg-gray-50 border-t border-gray-200">
                  <td className="px-4 py-3 text-sm font-bold text-gray-800 border-r border-gray-200"></td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-800 border-r border-gray-200"></td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-800 border-r border-gray-200"></td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-800 border-r border-gray-200"></td>
                  <td className="px-4 py-3 text-sm font-bold text-gray-800">
                    合计 {formatMoney(bill.amount)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1 p-3 rounded-lg bg-gray-50">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-800 min-h-[20px]">{value}</span>
    </div>
  );
}

function formatUnitPrice(n: number): string {
  const rounded = Math.round(n * 100) / 100;
  if (Math.abs(rounded - n) < 0.0001) {
    return rounded.toFixed(2);
  }
  return n.toFixed(4);
}
