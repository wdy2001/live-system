"""Task 6 验证脚本 - Dashboard API & 路由注册"""
import sys
import json
from app import create_app
from extensions import db
from models import Bill, RepairRequest, Household

app = create_app("development")
client = app.test_client()

results = []

def login_demo():
    resp = client.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.get_json()}"
    data = resp.get_json()
    return data["access_token"] if "access_token" in data else data.get("token")

def check(name, condition, detail=""):
    ok = bool(condition)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    return ok

print("\n" + "=" * 60)
print("Task 6 验证 - Dashboard API & 路由注册")
print("=" * 60)

with app.app_context():
    token = login_demo()
    auth_headers = {"Authorization": f"Bearer {token}"}

    # ===== TR-6.1 Dashboard API =====
    print("\n=== TR-6.1 Dashboard API 核心字段 ===")
    tr61_all = True

    resp = client.get("/api/dashboard", headers=auth_headers)
    tr61_all &= check("HTTP 200", resp.status_code == 200, f"实际={resp.status_code}")

    data = resp.get_json() or {}
    print(f"  响应 keys: {list(data.keys())}")

    # unpaid_total: float，待缴总额 = demo 的 unpaid 账单 sum(amount)
    has_unpaid_total = "unpaid_total" in data
    tr61_all &= check("包含 unpaid_total 字段", has_unpaid_total)
    if has_unpaid_total:
        unpaid_total = data["unpaid_total"]
        is_float = isinstance(unpaid_total, (int, float))
        tr61_all &= check("unpaid_total 是 float 类型", is_float, f"类型={type(unpaid_total).__name__}, 值={unpaid_total}")

        # 计算期望值
        demo_households = Household.query.join(Household.user).filter_by(username="demo").all()
        hh_ids = [h.id for h in demo_households]
        expected_unpaid = sum(
            float(b.amount) for b in Bill.query.filter(
                Bill.household_id.in_(hh_ids), Bill.status == "unpaid"
            ).all()
        )
        match = abs(float(unpaid_total) - expected_unpaid) < 0.01
        tr61_all &= check("unpaid_total 值正确 (sum of unpaid bills)", match,
                         f"实际={unpaid_total}, 期望={expected_unpaid}")

    # this_month_usage: dict，含 electricity/water/gas（最近一期用量）
    has_this_month = "this_month_usage" in data
    tr61_all &= check("包含 this_month_usage 字段", has_this_month)
    if has_this_month:
        tmu = data["this_month_usage"]
        is_dict = isinstance(tmu, dict)
        tr61_all &= check("this_month_usage 是 dict 类型", is_dict, f"类型={type(tmu).__name__}")
        if is_dict:
            has_keys = all(k in tmu for k in ("electricity", "water", "gas"))
            tr61_all &= check("this_month_usage 包含 electricity/water/gas 三个键", has_keys,
                             f"keys={list(tmu.keys())}")
            if has_keys:
                print(f"    this_month_usage = {tmu}")

    # trends: 长度=6 的数组
    has_trends = "trends" in data
    tr61_all &= check("包含 trends 字段", has_trends)
    if has_trends:
        trends = data["trends"]
        is_list = isinstance(trends, list)
        tr61_all &= check("trends 是 list 类型", is_list, f"类型={type(trends).__name__}")
        if is_list:
            len6 = len(trends) == 6
            tr61_all &= check("trends 长度=6", len6, f"实际长度={len(trends)}")
            if len6:
                all_ok = True
                for i, item in enumerate(trends):
                    has_period = "period" in item
                    has_usage = "usage" in item
                    if not (has_period and has_usage):
                        all_ok = False
                        print(f"    trends[{i}] 缺少 period 或 usage: keys={list(item.keys())}")
                        break
                    usage = item["usage"]
                    has_usage_keys = all(k in usage for k in ("electricity", "water", "gas"))
                    if not has_usage_keys:
                        all_ok = False
                        print(f"    trends[{i}].usage 缺少 electricity/water/gas: keys={list(usage.keys())}")
                        break
                tr61_all &= check("trends 每个元素都有 period + usage{electricity,water,gas}", all_ok)
                if all_ok:
                    print(f"    trends 样例[0] = {trends[0]}")
                    print(f"    trends 样例[-1] = {trends[-1]}")

    # repair_stats: dict，含 pending/processing/resolved (种子数据应为 1/1/1)
    has_repair_stats = "repair_stats" in data
    tr61_all &= check("包含 repair_stats 字段", has_repair_stats)
    if has_repair_stats:
        rs = data["repair_stats"]
        is_dict = isinstance(rs, dict)
        tr61_all &= check("repair_stats 是 dict 类型", is_dict, f"类型={type(rs).__name__}")
        if is_dict:
            has_keys = all(k in rs for k in ("pending", "processing", "resolved"))
            tr61_all &= check("repair_stats 包含 pending/processing/resolved 三个键", has_keys,
                             f"keys={list(rs.keys())}")
            if has_keys:
                expected_rs = {"pending": 1, "processing": 1, "resolved": 1}
                match = (rs["pending"] == expected_rs["pending"] and
                        rs["processing"] == expected_rs["processing"] and
                        rs["resolved"] == expected_rs["resolved"])
                tr61_all &= check("repair_stats 值正确 1/1/1", match,
                                 f"实际={rs}, 期望={expected_rs}")

    results.append(("TR-6.1 Dashboard API 核心字段", tr61_all))

    # ===== TR-6.2 Health API =====
    print("\n=== TR-6.2 Health API ===")
    tr62_all = True

    resp = client.get("/api/health")
    tr62_all &= check("HTTP 200", resp.status_code == 200, f"实际={resp.status_code}")

    data = resp.get_json() or {}
    tr62_all &= check("status == ok", data.get("status") == "ok",
                     f"实际={data.get('status')}")
    tr62_all &= check("service == life-system", data.get("service") == "life-system",
                     f"实际={data.get('service')}")

    print(f"  响应: {data}")
    results.append(("TR-6.2 Health API", tr62_all))

    # ===== TR-6.3 路由注册验证 =====
    print("\n=== TR-6.3 路由注册验证 (/api 前缀) ===")
    tr63_all = True

    # POST /api/auth/login
    print("\n  [1] POST /api/auth/login (demo/demo123)")
    resp = client.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ auth_bp 在 /api/auth", ok, f"实际={resp.status_code}")

    # GET /api/households/mine
    print("\n  [2] GET /api/households/mine (带 token)")
    resp = client.get("/api/households/mine", headers=auth_headers)
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ households_bp 在 /api/households", ok, f"实际={resp.status_code}")

    # GET /api/bills
    print("\n  [3] GET /api/bills")
    resp = client.get("/api/bills", headers=auth_headers)
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ bills_bp 在 /api/bills", ok, f"实际={resp.status_code}")

    # GET /api/rules?type=electricity
    print("\n  [4] GET /api/rules?type=electricity")
    resp = client.get("/api/rules?type=electricity")
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ rules_bp 在 /api/rules", ok, f"实际={resp.status_code}")

    # GET /api/repairs
    print("\n  [5] GET /api/repairs (带 token)")
    resp = client.get("/api/repairs", headers=auth_headers)
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ repairs_bp 在 /api/repairs", ok, f"实际={resp.status_code}")

    # GET /api/dashboard
    print("\n  [6] GET /api/dashboard (带 token)")
    resp = client.get("/api/dashboard", headers=auth_headers)
    ok = resp.status_code == 200
    tr63_all &= check("  HTTP 200 ✓ dashboard_bp 在 /api/dashboard", ok, f"实际={resp.status_code}")

    results.append(("TR-6.3 路由注册验证", tr63_all))

# ===== TR-6.x 检查 routes/__init__.py =====
print("\n=== 检查 routes/__init__.py Blueprint 前缀 ===")
import inspect
from routes import register_routes
source = inspect.getsource(register_routes)
print(f"  register_routes 源代码:")
for line in source.strip().split("\n"):
    print(f"    {line.strip()}")

prefix_ok = True
for bp_name, expected_prefix in [
    ("auth_bp", "/api/auth"),
    ("households_bp", "/api/households"),
    ("bills_bp", "/api/bills"),
    ("rules_bp", "/api/rules"),
    ("repairs_bp", "/api/repairs"),
    ("dashboard_bp", "/api/dashboard"),
]:
    ok = f'url_prefix="{expected_prefix}"' in source or f"url_prefix='{expected_prefix}'" in source
    prefix_ok &= check(f"  {bp_name} → {expected_prefix}", ok,
                      f"{'✓' if ok else '✗ 未找到前缀'}")

results.append(("routes/__init__.py Blueprint 前缀检查", prefix_ok))

# ===== 汇总 =====
print("\n" + "=" * 60)
print("验证结果汇总：")
print("=" * 60)
all_pass = True
for name, ok in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    all_pass &= ok
print("=" * 60)
if all_pass:
    print("✅ 全部验证通过")
    sys.exit(0)
else:
    print("❌ 部分验证失败，需要修复")
    sys.exit(1)
