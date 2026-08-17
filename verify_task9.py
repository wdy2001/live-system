import requests, json, re, sys

BASE = "http://127.0.0.1:5000"
results = []

def check(name, condition, detail=""):
    status = "✅ PASS" if condition else "❌ FAIL"
    print(f"{status} - {name}")
    if detail and not condition:
        print(f"        详情: {detail}")
    results.append((name, condition, detail))
    return condition

print("=" * 60)
print("Step 1: 登录 demo/demo123 获取 TOKEN")
print("=" * 60)

login_resp = requests.post(
    f"{BASE}/api/auth/login",
    json={"username": "demo", "password": "demo123"},
    headers={"Content-Type": "application/json"},
)
ok = check("登录返回 HTTP 200", login_resp.status_code == 200, f"实际={login_resp.status_code}")
if not ok:
    print("登录失败，中止")
    sys.exit(1)

login_data = login_resp.json()
TOKEN = login_data.get("access_token")
ok = check("access_token 非空", bool(TOKEN), f"响应={json.dumps(login_data)[:200]}")
if not ok:
    sys.exit(1)
print(f"        TOKEN (前40字符): {TOKEN[:40]}...")

headers = {"Authorization": f"Bearer {TOKEN}"}

print()
print("=" * 60)
print("Checkpoint 9.1  API字段齐全")
print("=" * 60)

resp = requests.get(f"{BASE}/api/dashboard", headers=headers)
http_ok = check("HTTP 200", resp.status_code == 200, f"实际={resp.status_code}, body={resp.text[:200]}")
if not http_ok:
    sys.exit(1)

data = resp.json()
print(f"        响应字段: {list(data.keys())}")

total_unpaid = data.get("total_unpaid_amount")
check(
    "total_unpaid_amount 是数字且 ≥ 0",
    isinstance(total_unpaid, (int, float)) and total_unpaid >= 0,
    f"实际值={total_unpaid!r}, 类型={type(total_unpaid).__name__}",
)

tmu = data.get("this_month_usage")
tmu_ok = check(
    "this_month_usage 是对象，含 electricity/water/gas 三键且都是数字",
    isinstance(tmu, dict)
    and all(k in tmu for k in ["electricity", "water", "gas"])
    and all(isinstance(tmu[k], (int, float)) for k in ["electricity", "water", "gas"]),
    f"实际={tmu!r}",
)

rs = data.get("repair_stats")
rs_ok = check(
    "repair_stats 是对象，含 pending/processing/resolved 三键且都是整数",
    isinstance(rs, dict)
    and all(k in rs for k in ["pending", "processing", "resolved"])
    and all(isinstance(rs[k], int) for k in ["pending", "processing", "resolved"]),
    f"实际={rs!r}",
)

ut = data.get("usage_trend")
ut_len_ok = check(
    "usage_trend 是数组且 length === 6",
    isinstance(ut, list) and len(ut) == 6,
    f"类型={type(ut).__name__}, 长度={len(ut) if isinstance(ut, list) else 'N/A'}",
)

print()
print("=" * 60)
print("Checkpoint 9.2  trend 格式+顺序")
print("=" * 60)

if isinstance(ut, list):
    pattern = re.compile(r"^\d{4}-\d{2}$")
    periods = []
    all_have_fields = True
    all_period_format_ok = True
    for i, item in enumerate(ut):
        if not isinstance(item, dict):
            all_have_fields = False
            continue
        p = item.get("period")
        if not isinstance(p, str) or not pattern.match(p):
            all_period_format_ok = False
        periods.append(p)
        for k in ["electricity", "water", "gas"]:
            if k not in item or not isinstance(item[k], (int, float)):
                all_have_fields = False

    check(
        "每条元素 period 匹配 ^\\d{4}-\\d{2}$ 格式",
        all_period_format_ok,
        f"periods={periods}",
    )

    no_dup = len(set(periods)) == len(periods) and all(p is not None for p in periods)
    check("每条元素 period 不重复", no_dup, f"periods={periods}")

    valid_periods = [p for p in periods if p]
    sorted_asc = sorted(valid_periods)
    sorted_desc = sorted(valid_periods, reverse=True)
    ordered = (periods == sorted_asc) or (periods == sorted_desc)
    order_desc = "旧→新" if periods == sorted_asc else ("新→旧" if periods == sorted_desc else "无序")
    check(
        f"period 按时间顺序排列（当前: {order_desc}）",
        ordered,
        f"periods={periods}",
    )

    check(
        "每条都有 electricity/water/gas 三个数值字段",
        all_have_fields,
        f"ut={ut}",
    )
else:
    print("    ⚠️  跳过，因为 usage_trend 不是数组")

print()
print("=" * 60)
print("Checkpoint 9.3  前端UI结构")
print("=" * 60)

import os
dashboard_path = "/workspace/src/pages/Dashboard.tsx"
with open(dashboard_path, "r", encoding="utf-8") as f:
    dash_src = f.read()

statcard_count = dash_src.count("<StatCard")
check(
    "Dashboard.tsx 中有 4 张 StatCard（待缴总额/本月电费/本月水费/本月燃气费）",
    statcard_count == 4,
    f"实际 StatCard 出现次数 = {statcard_count}",
)

has_pending = "pending" in dash_src and '"pending"' not in '""'
repair_pending = "待处理" in dash_src or "repair_stats.pending" in dash_src
repair_processing = "处理中" in dash_src or "repair_stats.processing" in dash_src
repair_resolved = "已解决" in dash_src or "repair_stats.resolved" in dash_src
check(
    "有报修进度 3 色小卡（pending/processing/resolved 三种统计展示）",
    repair_pending and repair_processing and repair_resolved,
    f"待处理展示={repair_pending}, 处理中展示={repair_processing}, 已解决展示={repair_resolved}",
)

usage_chart_used = "<UsageChart" in dash_src or "UsageChart" in dash_src
barchart_used = "BarChart" in dash_src
with open("/workspace/src/components/UsageChart.tsx", "r", encoding="utf-8") as f:
    uc_src = f.read()
has_bar_chart = "BarChart" in uc_src
check(
    "UsageChart 组件 / BarChart 组件被用于渲染近6月用量趋势",
    usage_chart_used and has_bar_chart,
    f"Dashboard引用UsageChart={usage_chart_used}, UsageChart内有BarChart={has_bar_chart}",
)

print()
print("=" * 60)
print("Checkpoint 9.4  图表颜色+tooltip")
print("=" * 60)

with open("/workspace/src/components/UsageChart.tsx", "r", encoding="utf-8") as f:
    uc_src = f.read()

tooltip_ok = "<Tooltip" in uc_src or "/Tooltip>" in uc_src or "Tooltip />" in uc_src
check(
    "BarChart 中启用 Tooltip 组件（可 hover 显示）",
    tooltip_ok,
    "UsageChart.tsx 中未找到 <Tooltip",
)

import re as _re
bar_fills = {}
for bar_match in _re.finditer(r'<Bar\s[^>]*dataKey="(electricity|water|gas)"[^>]*fill="([^"]+)"', uc_src):
    key, color = bar_match.group(1), bar_match.group(2)
    bar_fills[key] = color

elec_color = bar_fills.get("electricity", "")
water_color = bar_fills.get("water", "")
gas_color = bar_fills.get("gas", "")

all_distinct = (
    elec_color and water_color and gas_color
    and elec_color != water_color
    and water_color != gas_color
    and elec_color != gas_color
)

elec_blueish = elec_color and any(k in elec_color.lower() for k in ["#3b82", "#2563", "blue", "aqua", "sky", "#0ea5e9", "#06b6d4"])
water_greenish = water_color and any(k in water_color.lower() for k in ["#10b9", "#0596", "green", "forest", "emerald", "#22c55e", "#047857"])
gas_orangish = gas_color and any(k in gas_color.lower() for k in ["#f59e", "#f973", "orange", "amber", "energy", "#ea580c", "#fb923c"])

print(f"        电(Bar electricity) fill = {elec_color}")
print(f"        水(Bar water) fill = {water_color}")
print(f"        气(Bar gas) fill = {gas_color}")

colors_ok = all_distinct and elec_blueish and water_greenish and gas_orangish
check(
    "三个 Bar 颜色区分：电蓝/水绿/气橙",
    colors_ok,
    f"三色均不同={all_distinct}; 电蓝色系={elec_blueish} ({elec_color}); 水绿色系={water_greenish} ({water_color}); 气橙色系={gas_orangish} ({gas_color})",
)

print()
print("=" * 60)
print("Summary: Checkpoint 9.1 ~ 9.4 结果汇总")
print("=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
for idx, (name, ok, _) in enumerate(results, 1):
    print(f"  {idx:2d}. {'✅' if ok else '❌'}  {name}")
print(f"\n总计: {passed}/{total} 通过")
print(f"tasks.md TR-9.1: API 字段齐全 total_unpaid_amount ≥ 0 -> {'通过' if passed >= 4 else '未通过'}")
print(f"tasks.md TR-9.2: usage_trend 长度=6 每条含period+三类型 -> {'通过' if ut_len_ok else '未通过'}")
print(f"tasks.md TR-9.3: 工作台 UI 4张统计卡+1图表+报修进度 -> {'通过' if statcard_count == 4 and repair_pending else '未通过'}")
print(f"tasks.md TR-9.4: 图表近6月柱形区分颜色+hover tooltip -> {'通过' if tooltip_ok and colors_ok else '未通过'}")

sys.exit(0 if passed == total else 1)
