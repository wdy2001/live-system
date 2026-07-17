import { useEffect, useState } from "react";
import { Wrench, Send, CheckCircle2, Clock, Loader2, Phone, Zap, Droplets, Flame, HelpCircle } from "lucide-react";
import api from "@/lib/api";
import type { RepairRequest, RepairType } from "@/types";
import { REPAIR_TYPE_LABEL, REPAIR_STATUS_META, UTILITY_META } from "@/lib/constants";
import { PageHeader } from "@/components/Layout";
import { SkeletonList } from "@/components/Skeleton";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

const REPAIR_TYPE_OPTIONS: Array<{ value: RepairType; icon: typeof Zap }> = [
  { value: "electricity", icon: Zap },
  { value: "water", icon: Droplets },
  { value: "gas", icon: Flame },
  { value: "other", icon: HelpCircle },
];

export default function Repair() {
  const { user } = useAuthStore();
  const [repairs, setRepairs] = useState<RepairRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  // 表单
  const [type, setType] = useState<RepairType>("electricity");
  const [description, setDescription] = useState("");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [urgency, setUrgency] = useState<"normal" | "urgent">("normal");
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    api.get("/repairs").then((r) => setRepairs(r.data.repairs)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { if (user?.phone) setPhone(user.phone); }, [user]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!description.trim()) { setError("请填写故障描述"); return; }
    if (!phone.trim()) { setError("请填写联系电话"); return; }
    setSubmitting(true);
    try {
      await api.post("/repairs", { type, description: description.trim(), phone: phone.trim(), urgency });
      setDescription("");
      setUrgency("normal");
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      load();
    } catch (err) {
      setError((err as { response?: { data?: { msg?: string } } })?.response?.data?.msg || "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <PageHeader title="故障报修" subtitle="提交报修工单，物业将尽快安排处理" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* 报修表单 */}
        <div className="lg:col-span-2">
          <form onSubmit={submit} className="card animate-fade-up">
            <h3 className="mb-5 flex items-center gap-2 font-serif text-lg font-bold text-forest-800">
              <Wrench className="h-5 w-5 text-forest-600" /> 提交报修
            </h3>

            {/* 报修类型 */}
            <div className="mb-4">
              <label className="label">报修类型</label>
              <div className="grid grid-cols-4 gap-2">
                {REPAIR_TYPE_OPTIONS.map((opt) => {
                  const active = type === opt.value;
                  const Icon = opt.icon;
                  const accent = opt.value !== "other" ? UTILITY_META[opt.value as "electricity"] : null;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setType(opt.value)}
                      className={cn(
                        "flex flex-col items-center gap-1.5 rounded-xl border p-3 text-xs font-medium transition",
                        active
                          ? "border-forest-500 bg-forest-50 text-forest-700"
                          : "border-forest-50 text-ink-muted hover:bg-cream",
                      )}
                    >
                      <Icon className={cn("h-5 w-5", active ? "text-forest-600" : accent?.text ?? "text-ink-muted")} />
                      {REPAIR_TYPE_LABEL[opt.value]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 故障描述 */}
            <div className="mb-4">
              <label className="label">故障描述</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="请描述故障现象、发生位置等，便于维修人员准备"
                className="input resize-none"
              />
            </div>

            {/* 联系电话 */}
            <div className="mb-4">
              <label className="label">联系电话</label>
              <div className="relative">
                <Phone className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
                <input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="维修人员将通过此号码联系您"
                  className="input pl-10"
                />
              </div>
            </div>

            {/* 紧急程度 */}
            <div className="mb-5">
              <label className="label">紧急程度</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setUrgency("normal")}
                  className={cn(
                    "flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium transition",
                    urgency === "normal" ? "border-forest-500 bg-forest-50 text-forest-700" : "border-forest-50 text-ink-muted hover:bg-cream",
                  )}
                >
                  普通
                </button>
                <button
                  type="button"
                  onClick={() => setUrgency("urgent")}
                  className={cn(
                    "flex-1 rounded-xl border px-4 py-2.5 text-sm font-medium transition",
                    urgency === "urgent" ? "border-clay-500 bg-clay-50 text-clay-600" : "border-forest-50 text-ink-muted hover:bg-cream",
                  )}
                >
                  紧急
                </button>
              </div>
            </div>

            {error && <p className="mb-4 rounded-lg bg-clay-50 px-3 py-2 text-sm text-clay-600">{error}</p>}
            {success && (
              <p className="mb-4 flex items-center gap-2 rounded-lg bg-forest-50 px-3 py-2 text-sm text-forest-700">
                <CheckCircle2 className="h-4 w-4" /> 报修工单已提交，我们将尽快处理
              </p>
            )}

            <button type="submit" disabled={submitting} className="btn-primary w-full">
              {submitting ? <><Loader2 className="h-4 w-4 animate-spin" /> 提交中</> : <><Send className="h-4 w-4" /> 提交工单</>}
            </button>
          </form>
        </div>

        {/* 工单列表 */}
        <div className="lg:col-span-3">
          <h3 className="mb-4 font-serif text-lg font-bold text-forest-800">我的报修记录</h3>
          {loading ? (
            <SkeletonList count={4} />
          ) : repairs.length === 0 ? (
            <div className="card flex flex-col items-center py-16 text-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-forest-50">
                <Wrench className="h-7 w-7 text-forest-500" />
              </div>
              <p className="text-sm text-ink-muted">还没有报修记录</p>
            </div>
          ) : (
            <div className="space-y-3">
              {repairs.map((r, i) => (
                <RepairCard key={r.id} repair={r} delay={i * 60} />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function RepairCard({ repair, delay }: { repair: RepairRequest; delay: number }) {
  const statusMeta = REPAIR_STATUS_META[repair.status];
  const accent = repair.type !== "other" ? UTILITY_META[repair.type as "electricity"] : null;

  const TypeIcon =
    repair.type === "electricity" ? Zap :
    repair.type === "water" ? Droplets :
    repair.type === "gas" ? Flame : HelpCircle;

  return (
    <div className="card card-hover animate-fade-up" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl",
            accent ? `${accent.bg} ${accent.text}` : "bg-forest-50 text-forest-600",
          )}>
            <TypeIcon className="h-4 w-4" />
          </span>
          <div>
            <p className="text-sm font-medium text-ink">{REPAIR_TYPE_LABEL[repair.type]}</p>
            <p className="text-xs text-ink-muted">{new Date(repair.created_at).toLocaleString("zh-CN")}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {repair.urgency === "urgent" && (
            <span className="chip bg-clay-50 text-clay-500">紧急</span>
          )}
          <span className={cn("chip", statusMeta.className)}>{statusMeta.label}</span>
        </div>
      </div>

      <p className="mt-3 text-sm text-ink-soft">{repair.description}</p>
      <div className="mt-3 flex items-center gap-2 text-xs text-ink-muted">
        <Phone className="h-3.5 w-3.5" /> {repair.phone}
      </div>

      {/* 进度条 */}
      <div className="mt-4 flex items-center gap-1">
        {(["pending", "processing", "resolved"] as const).map((s) => {
          const m = REPAIR_STATUS_META[s];
          const done = statusMeta.step >= m.step;
          return (
            <div key={s} className="flex flex-1 items-center gap-1">
              <div className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs",
                done ? "bg-forest-600 text-white" : "bg-forest-50 text-ink-muted",
              )}>
                {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock className="h-3 w-3" />}
              </div>
              <span className={cn("text-xs", done ? "text-ink" : "text-ink-muted")}>{m.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
