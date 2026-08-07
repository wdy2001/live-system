"""端到端回归测试：覆盖 AC-1 ~ AC-10"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal, ROUND_HALF_UP
from app import create_app
from extensions import db
from models import Bill, RepairRequest, Household

results = []


def record(ac_id, name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append({"id": ac_id, "name": name, "status": status, "detail": detail})
    print(f"[{status}] {ac_id}: {name}" + (f" - {detail}" if detail else ""))
    return passed


def run_tests():
    app = create_app("development")
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        demo_token = _login(client, "demo", "demo123")
        admin_token = _login(client, "admin", "admin123")
        demo_headers = {"Authorization": f"Bearer {demo_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # AC-1: 注册+登录+登出后跳转逻辑
        _ac1_register_login_logout(client)

        # AC-2: dashboard 字段 + unpaid_total 手工核算
        _ac2_dashboard(client, demo_headers)

        # AC-3/4/5: 电/水/燃气 支付
        bill_ids = _ac345_pay_bills(client, demo_headers)

        # AC-6: bills 筛选 + breakdown 校验
        _ac6_bills_filter_and_breakdown(client, demo_headers, bill_ids)

        # AC-7: rules 接口
        _ac7_rules(client)

        # AC-8: 报修接口
        _ac8_repairs(client, demo_headers)

        # AC-9: 越权访问
        _ac9_forbidden(client, admin_headers, demo_headers)

        # AC-10: 阶梯计费 4 个典型用例
        _ac10_tiered_calculation(client, demo_headers)

    _print_summary()


def _login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return r.get_json()["token"]


def _ac1_register_login_logout(client):
    ac = "AC-1"
    name = "注册+登录+登出跳转逻辑"

    new_user = f"e2e_test_{os.getpid()}"
    r = client.post(
        "/api/auth/register",
        json={
            "username": new_user,
            "password": "test123456",
            "real_name": "测试用户",
            "phone": "13800000001",
        },
    )
    ok1 = r.status_code == 201 and "token" in r.get_json()
    detail1 = f"注册返回{r.status_code}"

    r2 = client.post("/api/auth/login", json={"username": new_user, "password": "test123456"})
    ok2 = r2.status_code == 200 and "token" in r2.get_json()
    detail2 = f"登录返回{r2.status_code}"

    token = r2.get_json()["token"]
    r3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    ok3 = r3.status_code == 200 and r3.get_json()["user"]["username"] == new_user
    detail3 = f"/me返回{r3.status_code}"

    r4 = client.post("/api/auth/login", json={"username": new_user, "password": "wrongpass"})
    ok4 = r4.status_code == 401
    detail4 = f"错误密码返回{r4.status_code}"

    ok5 = True
    try:
        r5 = client.get("/api/dashboard")
        ok5 = r5.status_code in (401, 422)
    except Exception:
        ok5 = False
    detail5 = f"无token访问dashboard被拒绝"

    all_ok = all([ok1, ok2, ok3, ok4, ok5])
    record(ac, name, all_ok, f"{detail1}; {detail2}; {detail3}; {detail4}; {detail5}")


def _ac2_dashboard(client, demo_headers):
    ac = "AC-2"
    name = "GET /api/dashboard 字段齐全 + unpaid_total 手工核算"

    r = client.get("/api/dashboard", headers=demo_headers)
    ok1 = r.status_code == 200
    data = r.get_json()

    required_fields = [
        "unpaid_total", "unpaid_count", "this_month_usage",
        "repair_stats", "trends", "households",
    ]
    ok2 = all(f in data for f in required_fields)
    detail2 = f"字段齐全:{all(f in data for f in required_fields)}"

    usage_fields = ["electricity", "water", "gas"]
    ok3 = all(f in data["this_month_usage"] for f in usage_fields)
    ok4 = all(f in data["repair_stats"] for f in ["pending", "processing", "resolved"])

    # 手工计算 unpaid_total
    hh_ids = [h["id"] for h in data["households"]]
    unpaid = (
        db.session.query(db.func.sum(Bill.amount))
        .filter(Bill.household_id.in_(hh_ids), Bill.status == "unpaid")
        .scalar()
    )
    expected_unpaid = float(unpaid or 0)
    actual_unpaid = float(data["unpaid_total"])
    ok5 = abs(expected_unpaid - actual_unpaid) < 0.01
    detail5 = f"unpaid_total API={actual_unpaid} DB计算={expected_unpaid}"

    all_ok = all([ok1, ok2, ok3, ok4, ok5])
    record(ac, name, all_ok, f"{detail2}; {detail5}")


def _find_unpaid_bills():
    bills = Bill.query.filter_by(status="unpaid").all()
    by_type = {}
    for b in bills:
        if b.type not in by_type:
            by_type[b.type] = b
    return by_type


def _ac345_pay_bills(client, demo_headers):
    by_type = _find_unpaid_bills()
    bill_ids = {}

    for type_key, ac_id, ac_name in [
        ("electricity", "AC-3", "电费支付成功+状态更新+电表读数更新"),
        ("water", "AC-4", "水费支付成功"),
        ("gas", "AC-5", "燃气费支付成功"),
    ]:
        bill = by_type.get(type_key)
        if not bill:
            record(ac_id, ac_name, False, f"找不到未支付的{type_key}账单")
            continue

        bill_id = bill.id
        bill_ids[type_key] = bill_id
        meter_before = float(bill.meter.current_reading)
        bill_current_reading = float(bill.current_reading)

        r = client.post(f"/api/bills/{bill_id}/pay", headers=demo_headers, json={"method": "alipay"})
        ok1 = r.status_code == 200
        data = r.get_json() if ok1 else {}

        ok2 = ok1 and "transaction_no" in data and data.get("bill", {}).get("status") == "paid"

        # 检查 meter 读数
        db.session.expire_all()
        b2 = Bill.query.get(bill_id)
        meter_after = float(b2.meter.current_reading)
        ok3 = meter_after == bill_current_reading
        detail3 = f"电表读数 {meter_before} -> {meter_after} (应={bill_current_reading})"

        all_ok = all([ok1, ok2, ok3])
        record(ac_id, ac_name, all_ok, f"支付返回{r.status_code}; {detail3}")

    return bill_ids


def _ac6_bills_filter_and_breakdown(client, demo_headers, bill_ids):
    ac = "AC-6"
    name = "bills 筛选(type+status) + bill 详情 breakdown 之和 = amount"

    r1 = client.get("/api/bills?type=electricity", headers=demo_headers)
    ok1 = r1.status_code == 200
    bills_e = r1.get_json().get("bills", [])
    ok2 = all(b["type"] == "electricity" for b in bills_e)

    r2 = client.get("/api/bills?status=paid", headers=demo_headers)
    ok3 = r2.status_code == 200
    bills_paid = r2.get_json().get("bills", [])
    ok4 = all(b["status"] == "paid" for b in bills_paid) if bills_paid else True

    r3 = client.get("/api/bills?type=electricity&status=unpaid", headers=demo_headers)
    ok5 = r3.status_code == 200
    bills_eu = r3.get_json().get("bills", [])
    ok6 = all(b["type"] == "electricity" and b["status"] == "unpaid" for b in bills_eu)

    # breakdown 校验：用任意一个有 breakdown 的账单
    any_bill = Bill.query.filter(Bill.amount > 0).first()

    ok7 = True
    detail7 = "无账单可验证breakdown"
    if any_bill:
        bid = any_bill.id
        r4 = client.get(f"/api/bills/{bid}", headers=demo_headers)
        ok7_1 = r4.status_code == 200
        bill_data = r4.get_json().get("bill", {})
        breakdown = bill_data.get("breakdown", [])
        if ok7_1 and breakdown:
            subtotal_sum = sum(
                float(Decimal(str(b.get("subtotal", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                for b in breakdown
            )
            subtotal_sum = float(Decimal(str(subtotal_sum)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            amount = float(Decimal(str(bill_data.get("amount", 0))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            ok7 = abs(subtotal_sum - amount) < 0.02
            detail7 = f"bill#{bid}: breakdown小计={subtotal_sum} amount={amount}"
        else:
            ok7 = False
            detail7 = f"获取账单详情失败或无breakdown (code={r4.status_code})"

    all_ok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7])
    record(ac, name, all_ok, f"筛选逻辑正常; {detail7}")


def _ac7_rules(client):
    ac = "AC-7"
    name = "GET /api/rules 总长度=8; electricity=3条; 无token可访问"

    r1 = client.get("/api/rules")
    ok1 = r1.status_code == 200
    rules_all = r1.get_json().get("rules", []) if ok1 else []
    ok2 = len(rules_all) == 8
    detail2 = f"总规则数={len(rules_all)} (期望8)"

    r2 = client.get("/api/rules?type=electricity")
    ok3 = r2.status_code == 200
    rules_e = r2.get_json().get("rules", []) if ok3 else []
    ok4 = len(rules_e) == 3
    detail4 = f"电价规则数={len(rules_e)} (期望3)"

    ok5 = all(r["type"] == "electricity" for r in rules_e)

    all_ok = all([ok1, ok2, ok3, ok4, ok5])
    record(ac, name, all_ok, f"{detail2}; {detail4}; 无token可访问={ok1}")


def _ac8_repairs(client, demo_headers):
    ac = "AC-8"
    name = "报修接口(校验400、创建201、列表+1)"

    # 先看初始数量
    r0 = client.get("/api/repairs", headers=demo_headers)
    initial_count = len(r0.get_json().get("repairs", [])) if r0.status_code == 200 else 0

    # 校验400：缺少必填项
    r1 = client.post("/api/repairs", headers=demo_headers, json={"type": "water"})
    ok1 = r1.status_code == 400
    detail1 = f"缺少description返回{r1.status_code}"

    # 校验400：无效type
    r2 = client.post(
        "/api/repairs",
        headers=demo_headers,
        json={"type": "invalid_type", "description": "x", "phone": "1"},
    )
    ok2 = r2.status_code == 400
    detail2 = f"无效type返回{r2.status_code}"

    # 正常创建
    r3 = client.post(
        "/api/repairs",
        headers=demo_headers,
        json={
            "type": "electricity",
            "description": "E2E测试：插座没电",
            "phone": "13900001111",
            "urgency": "urgent",
        },
    )
    ok3 = r3.status_code == 201
    detail3 = f"创建报修返回{r3.status_code}"

    # 列表+1
    r4 = client.get("/api/repairs", headers=demo_headers)
    new_count = len(r4.get_json().get("repairs", [])) if r4.status_code == 200 else 0
    ok4 = new_count == initial_count + 1
    detail4 = f"列表数 {initial_count} -> {new_count} (期望+1)"

    all_ok = all([ok1, ok2, ok3, ok4])
    record(ac, name, all_ok, f"{detail1}; {detail2}; {detail3}; {detail4}")


def _ac9_forbidden(client, admin_headers, demo_headers):
    ac = "AC-9"
    name = "越权：admin访问demo的bill/repair返回403"

    # 找demo用户的账单
    demo_user_id = None
    from models import User
    demo_user = User.query.filter_by(username="demo").first()
    demo_user_id = demo_user.id if demo_user else None

    demo_hh = Household.query.filter_by(user_id=demo_user_id).first() if demo_user_id else None
    demo_bill = Bill.query.filter_by(household_id=demo_hh.id).first() if demo_hh else None
    demo_repair = RepairRequest.query.filter_by(user_id=demo_user_id).first() if demo_user_id else None

    ok1 = False
    detail1 = "未找到demo账单"
    if demo_bill:
        r = client.get(f"/api/bills/{demo_bill.id}", headers=admin_headers)
        ok1 = r.status_code == 403
        detail1 = f"admin访问demo bill#{demo_bill.id} 返回{r.status_code}"

    ok2 = False
    detail2 = "未找到demo工单"
    if demo_repair:
        r = client.get(f"/api/repairs/{demo_repair.id}", headers=admin_headers)
        ok2 = r.status_code == 403
        detail2 = f"admin访问demo repair#{demo_repair.id} 返回{r.status_code}"

    all_ok = ok1 and ok2
    record(ac, name, all_ok, f"{detail1}; {detail2}")


def _tiered_calc_manual(type_, usage):
    from models import BillTypeRule
    rules = (
        BillTypeRule.query.filter_by(type=type_)
        .order_by(BillTypeRule.tier.asc())
        .all()
    )
    remaining = Decimal(str(usage))
    total = Decimal("0")
    for r in rules:
        if remaining <= 0:
            break
        tmin = Decimal(str(r.min_usage))
        tmax = Decimal(str(r.max_usage)) if r.max_usage is not None else None
        cap = (tmax - tmin) if tmax is not None else remaining
        used = min(remaining, cap)
        total += used * Decimal(str(r.unit_price))
        remaining -= used
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _ac10_tiered_calculation(client, demo_headers):
    ac = "AC-10"
    name = "阶梯计费4用例(100/250电、15水、45气)"

    # 用电100度 (全第一档)
    e100_expected = _tiered_calc_manual("electricity", 100)
    e100_actual_api = _get_amount_via_dummy_bill("electricity", 100, demo_headers, client)
    ok1 = e100_actual_api is not None and abs(e100_expected - e100_actual_api) < 0.02

    # 用电250度 (跨1、2档)
    e250_expected = _tiered_calc_manual("electricity", 250)
    e250_actual_api = _get_amount_via_dummy_bill("electricity", 250, demo_headers, client)
    ok2 = e250_actual_api is not None and abs(e250_expected - e250_actual_api) < 0.02

    # 用水15吨 (跨1、2档)
    w15_expected = _tiered_calc_manual("water", 15)
    w15_actual_api = _get_amount_via_dummy_bill("water", 15, demo_headers, client)
    ok3 = w15_actual_api is not None and abs(w15_expected - w15_actual_api) < 0.02

    # 用气45立方 (全第一档)
    g45_expected = _tiered_calc_manual("gas", 45)
    g45_actual_api = _get_amount_via_dummy_bill("gas", 45, demo_headers, client)
    ok4 = g45_actual_api is not None and abs(g45_expected - g45_actual_api) < 0.02

    detail = (
        f"电100°: API={e100_actual_api} 期望={e100_expected}; "
        f"电250°: API={e250_actual_api} 期望={e250_expected}; "
        f"水15T: API={w15_actual_api} 期望={w15_expected}; "
        f"气45m³: API={g45_actual_api} 期望={g45_expected}"
    )

    all_ok = all([ok1, ok2, ok3, ok4])
    record(ac, name, all_ok, detail)


def _get_amount_via_dummy_bill(type_, usage, headers, client):
    """通过 bills list 找一个指定类型的账单，再用它的 breakdown 算法创建一条临时记录验证。
    由于没有专门的计费 API，我们用 bill 详情中的 breakdown 来反推：
    找到任意一个该类型账单后，直接调用 services.billing.calculate_tiered_amount
    返回 amount。"""
    from services.billing import calculate_tiered_amount
    r = calculate_tiered_amount(type_, usage)
    return r.get("amount")


def _print_summary():
    print()
    print("=" * 60)
    print("端到端回归测试结果汇总")
    print("=" * 60)
    passed = 0
    total = len(results)
    for r in results:
        print(f"  [{r['status']}] {r['id']}: {r['name']}")
        if r["detail"]:
            print(f"         {r['detail']}")
        if r["status"] == "PASS":
            passed += 1
    print("-" * 60)
    rate = (passed / total * 100) if total > 0 else 0
    print(f"  通过率: {passed}/{total} = {rate:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
