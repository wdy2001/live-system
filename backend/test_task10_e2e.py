"""Task 10 E2E 综合测试脚本
覆盖: health/注册/登录/me/households/mine/dashboard/bills列表筛选分页+详情+支付+重复支付/rules全量+按type+example/repairs提交失败校验+列表+详情+403跨用户
"""
import os
import sys
import json
import random
import string
import re

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import User, Household, Meter, BillTypeRule as Rule, Bill, RepairRequest as Repair, Payment

PASSED = 0
FAILED = 0
ALL_CHECKS = []


def check(cond, name, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        ALL_CHECKS.append(("PASS", name, detail))
        print(f"  ✅ PASS: {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        ALL_CHECKS.append(("FAIL", name, detail))
        print(f"  ❌ FAIL: {name}" + (f"  ({detail})" if detail else ""))


def rand_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def main():
    global PASSED, FAILED
    app = create_app("development")

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            from seed import seed as run_seed
            run_seed()

    print("\n" + "=" * 70)
    print("  Task 10 E2E 综合测试开始")
    print("=" * 70)

    # ==================== 1. health ====================
    print("\n=== [1] Health 检查 ===")
    resp_health = client.get("/api/health")
    check(resp_health.status_code == 200, "GET /api/health HTTP 200", f"actual={resp_health.status_code}")
    health_data = resp_health.get_json() or {}
    check(health_data.get("status") == "ok", "health.status = ok", f"actual={health_data.get('status')}")
    check(health_data.get("service") == "life-system", "health.service = life-system")

    # ==================== 2. 注册新用户 + 登录 + me ====================
    print("\n=== [2] 注册 + 登录 + me ===")
    username = f"e2e_{rand_suffix()}"
    password = "test123456"
    resp_reg = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "confirm_password": password,
            "real_name": "E2E Test",
            "phone": "13900000001",
        },
    )
    reg_data = resp_reg.get_json() or {}
    check(resp_reg.status_code == 201, "注册 HTTP 201", f"actual={resp_reg.status_code}")
    check("access_token" in reg_data and len(reg_data["access_token"]) > 0, "注册返回 access_token")
    check("user" in reg_data and reg_data["user"].get("id", 0) > 0, "注册返回 user.id>0", f"id={reg_data.get('user',{}).get('id')}")
    e2e_user_id = reg_data["user"]["id"]
    e2e_token = reg_data["access_token"]
    e2e_headers = {"Authorization": f"Bearer {e2e_token}"}

    # 登录
    resp_login = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    login_data = resp_login.get_json() or {}
    check(resp_login.status_code == 200, "登录 HTTP 200", f"actual={resp_login.status_code}")
    check("access_token" in login_data and len(login_data["access_token"]) > 10, "登录返回 access_token 非空")
    check(login_data.get("user", {}).get("username") == username, "登录返回 username 匹配")

    # me 接口
    resp_me = client.get("/api/auth/me", headers=e2e_headers)
    check(resp_me.status_code == 200, "GET /api/auth/me HTTP 200", f"actual={resp_me.status_code}")
    me_data = resp_me.get_json() or {}
    check("user" in me_data, "me 返回 user 字段")
    check(me_data["user"].get("id") == e2e_user_id, "me 返回 user.id 匹配")
    check(me_data["user"].get("username") == username, "me 返回 username 匹配")

    # ==================== 3. demo 登录 + households/mine ====================
    print("\n=== [3] demo 登录 + households/mine ===")
    resp_demo = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo123"},
    )
    demo_data = resp_demo.get_json() or {}
    check(resp_demo.status_code == 200, "demo 登录 HTTP 200")
    demo_token = demo_data["access_token"]
    demo_headers = {"Authorization": f"Bearer {demo_token}"}
    demo_user_id = demo_data["user"]["id"]

    # households/mine
    resp_hh = client.get("/api/households/mine", headers=demo_headers)
    check(resp_hh.status_code == 200, "GET /api/households/mine HTTP 200", f"actual={resp_hh.status_code}")
    hh_data = resp_hh.get_json() or {}
    check("households" in hh_data, "households/mine 返回 households 字段")
    households = hh_data["households"]
    check(len(households) >= 1, "demo 用户至少 1 个户号", f"actual={len(households)}")
    hh0 = households[0]
    check("household_no" in hh0, "户号包含 household_no 字段")
    check("meters" in hh0 and len(hh0["meters"]) == 3, "户号包含 3 类表计", f"actual={len(hh0.get('meters',[]))}")
    meter_types = sorted([m["type"] for m in hh0["meters"]])
    check(meter_types == ["electricity", "gas", "water"], "3 类表计类型正确", f"types={meter_types}")

    # ==================== 4. dashboard ====================
    print("\n=== [4] Dashboard ===")
    resp_dash = client.get("/api/dashboard", headers=demo_headers)
    check(resp_dash.status_code == 200, "GET /api/dashboard HTTP 200", f"actual={resp_dash.status_code}")
    dash = resp_dash.get_json() or {}

    check("unpaid_total" in dash, "dashboard 包含 unpaid_total 字段")
    check(isinstance(dash.get("unpaid_total"), (int, float)), "unpaid_total 是数值类型")
    check(dash["unpaid_total"] >= 0, "unpaid_total >= 0", f"actual={dash['unpaid_total']}")

    check("repair_processing" in dash, "dashboard 包含 repair_processing 字段")
    check(isinstance(dash.get("repair_processing"), int), "repair_processing 是 int 类型")

    check("this_month_usage" in dash, "dashboard 包含 this_month_usage 字段")
    tmu = dash.get("this_month_usage", {})
    check("electricity" in tmu and "water" in tmu and "gas" in tmu,
          "this_month_usage 含 electricity/water/gas 键")

    check("monthly_usage" in dash, "dashboard 包含 monthly_usage 字段")
    trends = dash.get("monthly_usage", [])
    check(isinstance(trends, list), "monthly_usage 是 list")
    check(len(trends) >= 1, "monthly_usage 长度 >= 1", f"len={len(trends)}")
    if trends:
        first_period = trends[0].get("period", "")
        check(bool(re.match(r"^\d{4}-\d{2}$", first_period)),
              "monthly_usage[0].period 格式 YYYY-MM", f"period={first_period}")
        check("electricity" in trends[0] and "water" in trends[0] and "gas" in trends[0],
              "monthly_usage[0] 包含三类用量键")

    # ==================== 5. bills 列表（筛选+分页）+ 详情 + 支付 + 重复支付拦截 ====================
    print("\n=== [5] Bills 列表 + 详情 + 支付 + 重复支付拦截 ===")

    # 5.1 bills 列表 + 按 type 筛选
    resp_el_bills = client.get(
        "/api/bills?type=electricity&page=1&per_page=5",
        headers=demo_headers,
    )
    check(resp_el_bills.status_code == 200, "GET /api/bills?type=electricity HTTP 200", f"actual={resp_el_bills.status_code}")
    el_bills_data = resp_el_bills.get_json() or {}
    check("bills" in el_bills_data, "返回 bills 字段")
    check("total" in el_bills_data, "返回 total 字段")
    check("page" in el_bills_data and el_bills_data["page"] == 1, "返回 page=1")
    check("per_page" in el_bills_data and el_bills_data["per_page"] == 5, "返回 per_page=5")
    el_bills = el_bills_data["bills"]
    check(len(el_bills) <= 5, "分页数量 <= per_page=5", f"actual={len(el_bills)}")
    if el_bills:
        check(all(b["type"] == "electricity" for b in el_bills), "按 type=electricity 筛选正确")
        check("household" in el_bills[0] and "meter" in el_bills[0], "bills 列表项含 household/meter")

    # 5.2 bills 按 status 筛选 + 分页
    resp_unpaid = client.get(
        "/api/bills?status=unpaid&page=1&per_page=20",
        headers=demo_headers,
    )
    check(resp_unpaid.status_code == 200, "查询 unpaid 账单 HTTP 200")
    unpaid_data = resp_unpaid.get_json() or {}
    unpaid_bills = unpaid_data.get("bills", [])
    check(len(unpaid_bills) > 0, "存在 unpaid 账单可供支付")
    if unpaid_bills:
        check(all(b["status"] == "unpaid" for b in unpaid_bills), "按 status=unpaid 筛选正确")

    target_bill = unpaid_bills[0]
    target_bill_id = target_bill["id"]
    target_amount = float(target_bill["amount"])
    check(target_bill["status"] == "unpaid", f"目标账单 bill_id={target_bill_id} status=unpaid")

    # 5.3 GET 账单详情
    resp_detail_bill = client.get(f"/api/bills/{target_bill_id}", headers=demo_headers)
    check(resp_detail_bill.status_code == 200, f"GET /api/bills/{target_bill_id} HTTP 200", f"actual={resp_detail_bill.status_code}")
    detail_bill = resp_detail_bill.get_json().get("bill", {})
    check("breakdown" in detail_bill, "账单详情包含 breakdown 字段")
    check("meter" in detail_bill and "household" in detail_bill, "账单详情包含 meter/household 关联")
    check(detail_bill.get("id") == target_bill_id, "账单详情 id 匹配")

    # 5.4 第 1 次支付 → 成功
    resp_pay1 = client.post(
        f"/api/bills/{target_bill_id}/pay",
        json={"method": "alipay"},
        headers=demo_headers,
    )
    check(resp_pay1.status_code == 200, "第 1 次支付 HTTP 200", f"actual={resp_pay1.status_code}")
    pay1_data = resp_pay1.get_json() or {}
    check(pay1_data.get("bill", {}).get("status") == "paid", "支付后 bill.status = paid")
    check("payment" in pay1_data, "支付响应包含 payment 对象")
    pay1_payment = pay1_data.get("payment", {})
    txn_no_1 = pay1_payment.get("transaction_no", "")
    check(txn_no_1.startswith("PAY"), "transaction_no 前缀 PAY", f"txn={txn_no_1[:10]}...")
    check(len(txn_no_1) >= 20, "transaction_no 长度 >= 20", f"len={len(txn_no_1)}")

    with app.app_context():
        payment_record = Payment.query.filter_by(transaction_no=txn_no_1).first()
        check(payment_record is not None, "Payment 表有对应 transaction_no 记录")
        if payment_record:
            check(abs(float(payment_record.amount) - target_amount) < 0.01,
                  "Payment.amount 与账单金额一致",
                  f"bill={target_amount}, payment={float(payment_record.amount)}")

    # 5.5 第 2 次支付 → 幂等 400
    resp_pay2 = client.post(
        f"/api/bills/{target_bill_id}/pay",
        json={"method": "wechat"},
        headers=demo_headers,
    )
    check(resp_pay2.status_code == 400, "第 2 次支付 HTTP 400 (幂等)", f"actual={resp_pay2.status_code}")
    pay2_msg = (resp_pay2.get_json() or {}).get("msg", "")
    check(pay2_msg == "该账单已支付", "重复支付错误消息 = '该账单已支付'", f"actual='{pay2_msg}'")

    # ==================== 6. rules 全量 + 按 type + example.amount 校验 ====================
    print("\n=== [6] Rules 全量 + 按 type + example ===")

    # 6.1 rules 全量
    resp_all_rules = client.get("/api/rules")
    check(resp_all_rules.status_code == 200, "GET /api/rules 全量 HTTP 200", f"actual={resp_all_rules.status_code}")
    all_rules_data = resp_all_rules.get_json() or {}
    all_rules = all_rules_data.get("rules", [])
    check(len(all_rules) == 9, "全量 rules 数量 = 9 (电3+水3+气3)", f"actual={len(all_rules)}")
    check("example" in all_rules_data, "全量 rules 返回 example 字段")

    # 6.2 电价规则
    resp_el = client.get("/api/rules?type=electricity")
    check(resp_el.status_code == 200, "GET /api/rules?type=electricity HTTP 200")
    el_data = resp_el.get_json() or {}
    el_rules = el_data.get("rules", [])
    check(len(el_rules) == 3, "电价规则数量 = 3", f"actual={len(el_rules)}")
    el_example = el_data.get("example", {})
    check(el_example.get("usage") == 250, "电价 example.usage = 250", f"actual={el_example.get('usage')}")
    el_amount = float(el_example.get("amount", 0))
    check(abs(el_amount - 150.5) < 0.02, "电价 example.amount ≈ 150.50",
          f"actual={el_amount}")
    check(len(el_example.get("breakdown", [])) >= 2, "电价 example.breakdown 长度 >= 2")

    # 6.3 水价规则
    resp_wt = client.get("/api/rules?type=water")
    check(resp_wt.status_code == 200, "GET /api/rules?type=water HTTP 200")
    wt_data = resp_wt.get_json() or {}
    check(len(wt_data.get("rules", [])) == 3, "水价规则数量 = 3", f"actual={len(wt_data.get('rules',[]))}")
    check(wt_data.get("example", {}).get("usage") == 15, "水价 example.usage = 15", f"actual={wt_data.get('example',{}).get('usage')}")

    # 6.4 气价规则
    resp_gs = client.get("/api/rules?type=gas")
    check(resp_gs.status_code == 200, "GET /api/rules?type=gas HTTP 200")
    gs_data = resp_gs.get_json() or {}
    check(len(gs_data.get("rules", [])) == 3, "气价规则数量 = 3", f"actual={len(gs_data.get('rules',[]))}")
    check(gs_data.get("example", {}).get("usage") == 350, "气价 example.usage = 350", f"actual={gs_data.get('example',{}).get('usage')}")

    # ==================== 7. repairs 提交（含失败校验）+ 列表 + 详情 + 403 跨用户 ====================
    print("\n=== [7] Repairs 提交失败校验 + 列表 + 详情 + 403 跨用户 ===")

    # 7.1 失败校验: 无效类型
    resp_bad_type = client.post(
        "/api/repairs",
        json={"type": "invalid_type", "description": "测试描述需要超过十个字才对哦", "phone": "13900000001", "urgency": "normal"},
        headers=demo_headers,
    )
    check(resp_bad_type.status_code == 400, "repair 无效类型 HTTP 400", f"actual={resp_bad_type.status_code}")
    check("报修类型无效" in (resp_bad_type.get_json() or {}).get("msg", ""), "无效类型错误消息正确")

    # 7.2 失败校验: 描述太短
    resp_short_desc = client.post(
        "/api/repairs",
        json={"type": "water", "description": "太短了", "phone": "13900000001", "urgency": "normal"},
        headers=demo_headers,
    )
    check(resp_short_desc.status_code == 400, "repair 描述太短 HTTP 400", f"actual={resp_short_desc.status_code}")
    check("故障描述长度需为 10-500 字" in (resp_short_desc.get_json() or {}).get("msg", ""), "描述太短错误消息正确")

    # 7.3 失败校验: 手机号格式错误
    resp_bad_phone = client.post(
        "/api/repairs",
        json={"type": "water", "description": "厨房水龙头漏水，已经持续3天了需要尽快维修", "phone": "12345", "urgency": "normal"},
        headers=demo_headers,
    )
    check(resp_bad_phone.status_code == 400, "repair 手机号格式错误 HTTP 400", f"actual={resp_bad_phone.status_code}")
    check("联系电话格式错误" in (resp_bad_phone.get_json() or {}).get("msg", ""), "手机号错误消息正确")

    # 7.4 成功创建 repair
    resp_create = client.post(
        "/api/repairs",
        json={
            "type": "water",
            "description": "厨房水龙头漏水，已经持续3天了需要尽快维修处理",
            "phone": "13900000002",
            "urgency": "normal",
        },
        headers=demo_headers,
    )
    check(resp_create.status_code == 201, "创建 repair HTTP 201", f"actual={resp_create.status_code}")
    created_repair = (resp_create.get_json() or {}).get("repair", {})
    repair_id = created_repair.get("id")
    check(repair_id is not None and repair_id > 0, "创建 repair 返回 id>0", f"id={repair_id}")
    check(created_repair.get("status") == "pending", "新建 repair.status = pending")
    check(created_repair.get("type") == "water", "新建 repair.type = water")

    # 7.5 repairs 列表
    resp_list = client.get("/api/repairs", headers=demo_headers)
    check(resp_list.status_code == 200, "GET /api/repairs HTTP 200")
    list_data = resp_list.get_json() or {}
    repairs_list = list_data.get("repairs", [])
    check(len(repairs_list) >= 1, "Repair 列表数量 >= 1", f"actual={len(repairs_list)}")

    # 7.6 repairs 按 status 过滤
    resp_pending = client.get("/api/repairs?status=pending", headers=demo_headers)
    check(resp_pending.status_code == 200, "GET /api/repairs?status=pending HTTP 200")
    pending_list = (resp_pending.get_json() or {}).get("repairs", [])
    check(all(r["status"] == "pending" for r in pending_list), "status=pending 过滤正确")

    # 7.7 repair 详情（本人）
    resp_detail = client.get(f"/api/repairs/{repair_id}", headers=demo_headers)
    check(resp_detail.status_code == 200, f"GET /api/repairs/{repair_id} 本人 HTTP 200", f"actual={resp_detail.status_code}")
    detail_data = (resp_detail.get_json() or {}).get("repair", {})
    check(detail_data.get("id") == repair_id, "repair 详情 id 匹配")
    check(detail_data.get("description") is not None, "repair 详情有 description")

    # 7.8 repair 详情 403 跨用户访问（用 e2e 用户访问 demo 的工单）
    resp_403 = client.get(f"/api/repairs/{repair_id}", headers=e2e_headers)
    check(resp_403.status_code == 403, f"跨用户访问 repair HTTP 403", f"actual={resp_403.status_code}")
    check("无权访问" in (resp_403.get_json() or {}).get("msg", ""), "403 错误消息含 '无权访问'")

    # bill 详情 403 跨用户访问
    resp_bill_403 = client.get(f"/api/bills/{target_bill_id}", headers=e2e_headers)
    check(resp_bill_403.status_code == 403, f"跨用户访问 bill HTTP 403", f"actual={resp_bill_403.status_code}")
    check("无权访问" in (resp_bill_403.get_json() or {}).get("msg", ""), "bill 403 错误消息正确")

    # ==================== 建表数检查（补充） ====================
    print("\n=== [8] 建表/数据量检查 ===")
    with app.app_context():
        user_count = User.query.count()
        check(user_count >= 3, "User 表记录数 >= 3 (admin/demo/e2e)", f"actual={user_count}")

        household_count = Household.query.count()
        check(household_count >= 2, "Household 表记录数 >= 2 (demo/e2e各1)", f"actual={household_count}")

        meter_count = Meter.query.count()
        check(meter_count >= 6, "Meter 表记录数 >= 6 (2户 × 3类)", f"actual={meter_count}")

        rule_count = Rule.query.count()
        check(rule_count == 9, "Rule 表记录数 = 9 (电3+水3+气3)", f"actual={rule_count}")

        bill_count = Bill.query.count()
        check(bill_count >= 18, "Bill 表记录数 >= 18 (至少 demo 的6期×3类)", f"actual={bill_count}")

        repair_count = Repair.query.count()
        check(repair_count >= 1, "Repair 表记录数 >= 1", f"actual={repair_count}")

    # ==================== 汇总 ====================
    print("\n" + "=" * 70)
    print(f"  E2E 综合测试结果: {PASSED} 通过, {FAILED} 失败 / 共 {PASSED + FAILED} 项检查")
    print("=" * 70)
    if FAILED > 0:
        print("\n失败用例:")
        for status, name, detail in ALL_CHECKS:
            if status == "FAIL":
                print(f"  ❌ {name}" + (f"  ({detail})" if detail else ""))
        print()
        return False
    else:
        print()
        print("ALL E2E TESTS PASSED")
        return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
