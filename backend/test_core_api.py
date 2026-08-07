"""核心 API 综合验证：Dashboard + Bills + Rules + Repairs
合并验证任务 5 (TR-5.1/5.2/5.3/5.4) 与任务 6 (TR-6.1/6.2/6.3/6.4)
"""
import os
import sys
import json
from collections import Counter

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from seed import seed as run_seed
from extensions import db
from models import User, Household, Bill, RepairRequest, Meter, BillTypeRule

FAILURES = []

TR5_RESULTS = {"TR-5.1": None, "TR-5.2": None, "TR-5.3": None, "TR-5.4": None}
TR6_RESULTS = {"TR-6.1": None, "TR-6.2": None, "TR-6.3": None, "TR-6.4": None}


def _print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _log_failure(name, req_url, req_method, req_body, resp_status, resp_body, extra=None):
    FAILURES.append({
        "name": name,
        "req_url": req_url,
        "req_method": req_method,
        "req_body": req_body,
        "resp_status": resp_status,
        "resp_body": resp_body,
        "extra": extra,
    })


def _check(name, cond, expected, actual, req_url=None, req_method=None, req_body=None,
           resp_status=None, resp_body=None, extra=None):
    mark = "✅ PASS" if cond else "❌ FAIL"
    print(f"  [{mark}] {name}")
    if not cond:
        print(f"        期望: {expected}")
        print(f"        实际: {actual}")
        _log_failure(name, req_url, req_method, req_body, resp_status, resp_body, extra)
    return cond


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"} if token else {}


def run():
    _print_section("初始化数据库与种子数据")
    run_seed()
    print("  数据库初始化完成")

    app = create_app()

    with app.test_client() as c:
        demo_token = None
        admin_token = None
        demo_id = None
        admin_id = None

        # ======================== 登录准备 ========================
        _print_section("准备：登录获取 Token")

        r = c.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
        body = r.get_json(silent=True) or {}
        demo_token = body.get("token")
        demo_id = body.get("user", {}).get("id") if body.get("user") else None
        print(f"  demo 登录 -> HTTP {r.status_code}, token={'set' if demo_token else 'missing'}, demo_id={demo_id}")

        r = c.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        body = r.get_json(silent=True) or {}
        admin_token = body.get("token")
        admin_id = body.get("user", {}).get("id") if body.get("user") else None
        print(f"  admin 登录 -> HTTP {r.status_code}, token={'set' if admin_token else 'missing'}, admin_id={admin_id}")

        h_demo = _auth_headers(demo_token)
        h_admin = _auth_headers(admin_token)

        # ============================================================
        # Part A — Dashboard (任务5 TR-5.1)
        # ============================================================
        _print_section("Part A — Dashboard (TR-5.1)")
        r = c.get("/api/dashboard", headers=h_demo)
        body = r.get_json(silent=True) or {}
        print(f"  GET /api/dashboard -> HTTP {r.status_code}")

        a_checks = []

        a1 = _check(
            "A1. HTTP 状态码 = 200",
            r.status_code == 200, 200, r.status_code,
            "/api/dashboard", "GET", None, r.status_code, body,
        )
        a_checks.append(a1)

        required_fields = ["unpaid_total", "unpaid_count", "this_month_usage",
                           "repair_stats", "trends", "households"]
        for f in required_fields:
            ok = _check(
                f"A1. 字段存在: {f}",
                f in body, f"body 含 {f}", f"{f} in body keys: {list(body.keys())}",
                "/api/dashboard", "GET", None, r.status_code, body,
            )
            a_checks.append(ok)

        tmu = body.get("this_month_usage", {})
        for k in ("electricity", "water", "gas"):
            ok = _check(
                f"A1. this_month_usage 含 {k}",
                k in tmu, f"含 {k}", f"keys: {list(tmu.keys())}",
                "/api/dashboard", "GET", None, r.status_code, body,
            )
            a_checks.append(ok)

        rs = body.get("repair_stats", {})
        for k in ("pending", "processing", "resolved"):
            ok = _check(
                f"A1. repair_stats 含 {k}",
                k in rs, f"含 {k}", f"keys: {list(rs.keys())}",
                "/api/dashboard", "GET", None, r.status_code, body,
            )
            a_checks.append(ok)

        trends = body.get("trends", [])
        ok = _check(
            "A1. trends 长度 = 6",
            isinstance(trends, list) and len(trends) == 6,
            "length=6",
            f"type={type(trends).__name__}, len={len(trends) if isinstance(trends, list) else 'N/A'}",
            "/api/dashboard", "GET", None, r.status_code, body,
        )
        a_checks.append(ok)

        with app.app_context():
            demo_user = User.query.get(demo_id)
            hh_ids = [h.id for h in Household.query.filter_by(user_id=demo_id).all()]

            from sqlalchemy import func
            from sqlalchemy import text
            sql = text(
                "SELECT COALESCE(SUM(amount),0) as s FROM bills "
                "WHERE status='unpaid' AND household_id IN "
                "(SELECT id FROM households WHERE user_id=:uid)"
            )
            raw_sum = db.session.execute(sql, {"uid": demo_id}).scalar() or 0
            raw_total = float(raw_sum)

            api_total = float(body.get("unpaid_total", 0))
            ok = _check(
                f"A1. unpaid_total 与原始 SQL 查询一致 (原始={raw_total})",
                abs(api_total - raw_total) <= 0.01,
                f"≈ {raw_total}",
                f"{api_total}",
                "/api/dashboard", "GET", None, r.status_code, body,
                extra=f"raw SQL sum = {raw_total}, api returned = {api_total}",
            )
            a_checks.append(ok)

            for status_key in ("pending", "processing", "resolved"):
                expected_count = RepairRequest.query.filter_by(
                    user_id=demo_id, status=status_key
                ).count()
                actual_count = int(rs.get(status_key, -1))
                ok = _check(
                    f"A1. repair_stats.{status_key} = {expected_count}",
                    actual_count == expected_count,
                    expected_count, actual_count,
                    "/api/dashboard", "GET", None, r.status_code, body,
                )
                a_checks.append(ok)

        TR5_RESULTS["TR-5.1"] = all(a_checks)

        # ============================================================
        # Part B — Bills 列表与筛选 (任务5 TR-5.2)
        # ============================================================
        _print_section("Part B — Bills 列表与筛选 (TR-5.2)")
        b_checks = []

        r = c.get("/api/bills?type=water", headers=h_demo)
        body = r.get_json(silent=True) or {}
        bills_water = body.get("bills", []) or []
        print(f"  B1. GET /api/bills?type=water -> HTTP {r.status_code}, count={len(bills_water)}")

        ok = _check("B1. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/bills?type=water", "GET", None, r.status_code, body)
        b_checks.append(ok)
        all_water = all(b.get("type") == "water" for b in bills_water)
        ok = _check(
            "B1. 列表中所有 bills.type == 'water'",
            all_water and len(bills_water) > 0,
            "全部 type=water 且非空",
            f"count={len(bills_water)}, types={[b.get('type') for b in bills_water[:5]]}",
            "/api/bills?type=water", "GET", None, r.status_code, body,
        )
        b_checks.append(ok)

        r = c.get("/api/bills?type=electricity&status=unpaid", headers=h_demo)
        body = r.get_json(silent=True) or {}
        bills_eu = body.get("bills", []) or []
        print(f"  B2. GET /api/bills?type=electricity&status=unpaid -> HTTP {r.status_code}, count={len(bills_eu)}")

        ok = _check("B2. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/bills?type=electricity&status=unpaid", "GET", None, r.status_code, body)
        b_checks.append(ok)
        all_eu = all(
            b.get("type") == "electricity" and b.get("status") == "unpaid"
            for b in bills_eu
        )
        ok = _check(
            "B2. 列表全部满足 type=electricity AND status=unpaid",
            all_eu and len(bills_eu) > 0,
            "全部匹配且非空",
            f"count={len(bills_eu)}, sample types={[b.get('type') for b in bills_eu[:3]]}, "
            f"statuses={[b.get('status') for b in bills_eu[:3]]}",
            "/api/bills?type=electricity&status=unpaid", "GET", None, r.status_code, body,
        )
        b_checks.append(ok)

        r = c.get("/api/bills?status=paid", headers=h_demo)
        body = r.get_json(silent=True) or {}
        bills_paid = body.get("bills", []) or []
        print(f"  B3. GET /api/bills?status=paid -> HTTP {r.status_code}, count={len(bills_paid)}")

        ok = _check("B3. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/bills?status=paid", "GET", None, r.status_code, body)
        b_checks.append(ok)
        all_paid = all(b.get("status") == "paid" for b in bills_paid)
        ok = _check(
            "B3. 列表中所有 bills.status == 'paid'",
            all_paid and len(bills_paid) > 0,
            "全部 status=paid 且非空",
            f"count={len(bills_paid)}, statuses={[b.get('status') for b in bills_paid[:5]]}",
            "/api/bills?status=paid", "GET", None, r.status_code, body,
        )
        b_checks.append(ok)

        TR5_RESULTS["TR-5.2"] = all(b_checks)

        # ============================================================
        # Part C — Bill 详情 (任务5 TR-5.3前半)
        # ============================================================
        _print_section("Part C — Bill 详情 (TR-5.3 前半)")
        c_checks = []

        r = c.get("/api/bills?status=unpaid", headers=h_demo)
        body = r.get_json(silent=True) or {}
        unpaid_bills = body.get("bills", []) or []
        unpaid_bill_id = None
        unpaid_bill_amount = None
        if unpaid_bills:
            unpaid_bill_id = unpaid_bills[0]["id"]
            unpaid_bill_amount = float(unpaid_bills[0]["amount"])
        print(f"  选择 unpaid_bill_id = {unpaid_bill_id}, amount={unpaid_bill_amount}")

        c_passed_bill_id = unpaid_bill_id

        if unpaid_bill_id:
            r = c.get(f"/api/bills/{unpaid_bill_id}", headers=h_demo)
            body = r.get_json(silent=True) or {}
            bill_detail = body.get("bill", {}) or {}
            print(f"  C1. GET /api/bills/{unpaid_bill_id} -> HTTP {r.status_code}")

            ok = _check("C1. HTTP 200", r.status_code == 200, 200, r.status_code,
                        f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body)
            c_checks.append(ok)

            breakdown = bill_detail.get("breakdown", []) or []
            ok = _check(
                "C1. bill.breakdown 数组长度 >= 1",
                isinstance(breakdown, list) and len(breakdown) >= 1,
                "length >= 1",
                f"type={type(breakdown).__name__}, len={len(breakdown) if isinstance(breakdown, list) else 'N/A'}",
                f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body,
            )
            c_checks.append(ok)

            if isinstance(breakdown, list) and len(breakdown) >= 1:
                subtotal_sum = sum(float(x.get("subtotal", 0)) for x in breakdown)
                bill_amt = float(bill_detail.get("amount", 0))
                ok = _check(
                    f"C1. breakdown subtotal 之和 ({subtotal_sum}) ≈ bill.amount ({bill_amt})",
                    abs(subtotal_sum - bill_amt) <= 0.01,
                    f"差 <= 0.01 (bill.amount={bill_amt})",
                    f"sum(subtotal)={subtotal_sum}, diff={abs(subtotal_sum - bill_amt)}",
                    f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body,
                )
                c_checks.append(ok)

            hh = bill_detail.get("household") or {}
            ok = _check(
                "C1. bill.household 存在且 household_no 非空",
                isinstance(hh, dict) and bool(hh.get("household_no")),
                "household.household_no 非空",
                f"household={hh}",
                f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body,
            )
            c_checks.append(ok)

            meter = bill_detail.get("meter") or {}
            ok = _check(
                "C1. bill.meter 存在且 meter_no 非空",
                isinstance(meter, dict) and bool(meter.get("meter_no")),
                "meter.meter_no 非空",
                f"meter={meter}",
                f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body,
            )
            c_checks.append(ok)

            payment = bill_detail.get("payment")
            ok = _check(
                "C1. unpaid 账单 payment 为 None/不存在",
                payment is None,
                "payment 为 None",
                f"payment={payment}",
                f"/api/bills/{unpaid_bill_id}", "GET", None, r.status_code, body,
            )
            c_checks.append(ok)
        else:
            print("  ⚠️  无 unpaid 账单可用于 C 部分，跳过")
            c_checks.append(False)

        # ============================================================
        # Part D — Bill 支付流程 (任务5 TR-5.3后半 + TR-5.4)
        # ============================================================
        _print_section("Part D — Bill 支付流程 (TR-5.3 后半 + TR-5.4)")
        d_checks = []

        paid_bill_id = c_passed_bill_id
        d_payment_data = None

        if paid_bill_id:
            r = c.post(f"/api/bills/{paid_bill_id}/pay", headers=h_demo,
                       json={"method": "alipay"})
            body = r.get_json(silent=True) or {}
            print(f"  D1. POST /api/bills/{paid_bill_id}/pay -> HTTP {r.status_code}")
            print(f"      transaction_no={body.get('transaction_no')}, paid_at={body.get('paid_at')}")
            bill_after_pay = body.get("bill", {}) or {}

            ok = _check("D1. HTTP 200", r.status_code == 200, 200, r.status_code,
                        f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                        r.status_code, body)
            d_checks.append(ok)

            txn_no = body.get("transaction_no") or ""
            ok = _check(
                "D1. transaction_no 非空且前3字符 == 'PAY'",
                bool(txn_no) and txn_no[:3] == "PAY",
                "非空且前缀 PAY",
                f"transaction_no={txn_no!r}",
                f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                r.status_code, body,
            )
            d_checks.append(ok)

            paid_at = body.get("paid_at")
            ok = _check(
                "D1. paid_at 非空",
                bool(paid_at),
                "paid_at 非空",
                f"paid_at={paid_at!r}",
                f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                r.status_code, body,
            )
            d_checks.append(ok)

            ok = _check(
                "D1. 返回 bill.status == 'paid'",
                bill_after_pay.get("status") == "paid",
                "paid",
                f"status={bill_after_pay.get('status')!r}",
                f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                r.status_code, body,
            )
            d_checks.append(ok)

            d_payment_data = body

            r = c.get(f"/api/bills/{paid_bill_id}", headers=h_demo)
            body = r.get_json(silent=True) or {}
            bill_detail2 = body.get("bill", {}) or {}
            print(f"  D2. GET /api/bills/{paid_bill_id} 支付后 -> HTTP {r.status_code}")

            ok = _check(
                "D2. status == 'paid'",
                bill_detail2.get("status") == "paid",
                "paid",
                f"status={bill_detail2.get('status')!r}",
                f"/api/bills/{paid_bill_id}", "GET", None, r.status_code, body,
            )
            d_checks.append(ok)

            payment2 = bill_detail2.get("payment") or {}
            ok = _check(
                "D2. bill.payment 对象存在",
                isinstance(payment2, dict) and bool(payment2),
                "payment dict 非空",
                f"payment={payment2}",
                f"/api/bills/{paid_bill_id}", "GET", None, r.status_code, body,
            )
            d_checks.append(ok)

            if isinstance(payment2, dict):
                pay_amt = float(payment2.get("amount", 0))
                bill_amt2 = float(bill_detail2.get("amount", 0))
                ok = _check(
                    f"D2. payment.amount ({pay_amt}) == bill.amount ({bill_amt2})",
                    abs(pay_amt - bill_amt2) <= 0.01,
                    f"== {bill_amt2}",
                    f"payment.amount={pay_amt}",
                    f"/api/bills/{paid_bill_id}", "GET", None, r.status_code, body,
                )
                d_checks.append(ok)

            with app.app_context():
                bill_db = Bill.query.get(paid_bill_id)
                if bill_db:
                    meter_db = Meter.query.get(bill_db.meter_id)
                    meter_reading = float(meter_db.current_reading) if meter_db else None
                    bill_current = float(bill_db.current_reading)
                    ok = _check(
                        f"D3. Meter.current_reading ({meter_reading}) == Bill.current_reading ({bill_current})",
                        meter_reading is not None and abs(meter_reading - bill_current) <= 0.01,
                        f"== {bill_current}",
                        f"meter.current_reading={meter_reading}",
                        f"db check Meter.query.get({bill_db.meter_id})", None, None, None, None,
                    )
                    d_checks.append(ok)
                else:
                    d_checks.append(False)

            r = c.post(f"/api/bills/{paid_bill_id}/pay", headers=h_demo,
                       json={"method": "alipay"})
            body = r.get_json(silent=True) or {}
            msg = body.get("msg", "") or ""
            print(f"  D4. 重复支付 POST /api/bills/{paid_bill_id}/pay -> HTTP {r.status_code}, msg={msg!r}")

            ok = _check("D4. HTTP 400", r.status_code == 400, 400, r.status_code,
                        f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                        r.status_code, body)
            d_checks.append(ok)

            ok = _check(
                "D4. body.msg 含「已支付」",
                "已支付" in msg,
                "包含「已支付」",
                f"msg={msg!r}",
                f"/api/bills/{paid_bill_id}/pay", "POST", {"method": "alipay"},
                r.status_code, body,
            )
            d_checks.append(ok)

        r = c.get("/api/bills?status=unpaid", headers=h_demo)
        body = r.get_json(silent=True) or {}
        remaining_unpaid = body.get("bills", []) or []
        another_unpaid_id = None
        if remaining_unpaid:
            for b in remaining_unpaid:
                if b["id"] != paid_bill_id:
                    another_unpaid_id = b["id"]
                    break
        print(f"  D5. 另一条 unpaid bill id = {another_unpaid_id}")

        if another_unpaid_id and admin_token:
            r = c.post(f"/api/bills/{another_unpaid_id}/pay", headers=h_admin,
                       json={"method": "alipay"})
            body = r.get_json(silent=True) or {}
            msg = body.get("msg", "") or ""
            print(f"  D5. admin POST /api/bills/{another_unpaid_id}/pay -> HTTP {r.status_code}, msg={msg!r}")

            ok = _check("D5. HTTP 403 (越权)", r.status_code == 403, 403, r.status_code,
                        f"/api/bills/{another_unpaid_id}/pay", "POST", {"method": "alipay"},
                        r.status_code, body)
            d_checks.append(ok)

            ok = _check(
                "D5. body.msg 含「无权操作该账单」",
                "无权操作该账单" in msg,
                "包含「无权操作该账单」",
                f"msg={msg!r}",
                f"/api/bills/{another_unpaid_id}/pay", "POST", {"method": "alipay"},
                r.status_code, body,
            )
            d_checks.append(ok)
        else:
            print("  ⚠️  缺少另一条 unpaid bill 或 admin_token，跳过 D5")
            d_checks.append(False)

        tr53_ok = all(c_checks) and all(d_checks[:len(c_checks) + 3])
        TR5_RESULTS["TR-5.3"] = all(c_checks) and (len(d_checks) >= 3 and all(d_checks[:3]))
        TR5_RESULTS["TR-5.4"] = all(d_checks) if d_checks else False

        # ============================================================
        # Part E — 计费规则 (任务6 TR-6.1)
        # ============================================================
        _print_section("Part E — 计费规则 (TR-6.1)")
        e_checks = []

        r = c.get("/api/rules")
        body = r.get_json(silent=True) or {}
        rules_all = body.get("rules", []) or []
        print(f"  E1. GET /api/rules -> HTTP {r.status_code}, count={len(rules_all)}")

        ok = _check("E1. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/rules", "GET", None, r.status_code, body)
        e_checks.append(ok)

        ok = _check(
            "E1. rules 数组长度 == 8",
            len(rules_all) == 8,
            8, len(rules_all),
            "/api/rules", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        type_counts = Counter(r.get("type") for r in rules_all)
        ok = _check(
            f"E1. 按 type 聚合: electricity=3, water=2, gas=3 (实际: {dict(type_counts)})",
            type_counts.get("electricity") == 3 and type_counts.get("water") == 2 and type_counts.get("gas") == 3,
            "electricity=3, water=2, gas=3",
            f"{dict(type_counts)}",
            "/api/rules", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        r = c.get("/api/rules?type=gas")
        body = r.get_json(silent=True) or {}
        rules_gas = body.get("rules", []) or []
        print(f"  E2. GET /api/rules?type=gas -> HTTP {r.status_code}, count={len(rules_gas)}")

        ok = _check("E2. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/rules?type=gas", "GET", None, r.status_code, body)
        e_checks.append(ok)

        ok = _check(
            "E2. 长度 == 3",
            len(rules_gas) == 3,
            3, len(rules_gas),
            "/api/rules?type=gas", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        all_gas = all(r.get("type") == "gas" for r in rules_gas)
        ok = _check(
            "E2. 每条 type == gas",
            all_gas,
            "全部 type=gas",
            f"types={[r.get('type') for r in rules_gas]}",
            "/api/rules?type=gas", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        tiers = [r.get("tier") for r in rules_gas]
        ok = _check(
            f"E2. tier 按 1,2,3 升序 (实际 {tiers})",
            tiers == [1, 2, 3],
            "[1, 2, 3]",
            f"{tiers}",
            "/api/rules?type=gas", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        r = c.get("/api/rules")
        body = r.get_json(silent=True) or {}
        print(f"  E3. 无 token GET /api/rules -> HTTP {r.status_code}")

        ok = _check(
            "E3. 不带 token 也能访问 /api/rules -> 200 (公开接口)",
            r.status_code == 200,
            200, r.status_code,
            "/api/rules", "GET", None, r.status_code, body,
        )
        e_checks.append(ok)

        TR6_RESULTS["TR-6.1"] = all(e_checks)

        # ============================================================
        # Part F — 报修列表与创建 (任务6 TR-6.2/6.3/6.4)
        # ============================================================
        _print_section("Part F — 报修列表与创建 (TR-6.2 / 6.3 / 6.4)")
        f_checks = []
        repair_ids_before = []

        r = c.get("/api/repairs", headers=h_demo)
        body = r.get_json(silent=True) or {}
        repairs_before = body.get("repairs", []) or []
        repair_ids_before = [x.get("id") for x in repairs_before]
        created_before = [x.get("created_at") for x in repairs_before]
        print(f"  F1. GET /api/repairs -> HTTP {r.status_code}, count={len(repairs_before)}")

        ok = _check("F1. HTTP 200", r.status_code == 200, 200, r.status_code,
                    "/api/repairs", "GET", None, r.status_code, body)
        f_checks.append(ok)

        ok = _check(
            "F1. 列表 >= 3 条",
            len(repairs_before) >= 3,
            ">= 3",
            f"count={len(repairs_before)}",
            "/api/repairs", "GET", None, r.status_code, body,
        )
        f_checks.append(ok)

        sorted_desc = all(
            created_before[i] >= created_before[i + 1]
            for i in range(len(created_before) - 1)
        ) if len(created_before) >= 2 else True
        ok = _check(
            f"F1. 按 created_at 降序 (最新在前)",
            sorted_desc,
            "降序排列",
            f"created_at 序列: {created_before}",
            "/api/repairs", "GET", None, r.status_code, body,
        )
        f_checks.append(ok)

        r = c.post("/api/repairs", headers=h_demo,
                   json={"type": "water", "description": "", "phone": "138"})
        body = r.get_json(silent=True) or {}
        msg = body.get("msg", "") or ""
        print(f"  F2. POST 空描述 -> HTTP {r.status_code}, msg={msg!r}")

        ok = _check("F2. HTTP 400", r.status_code == 400, 400, r.status_code,
                    "/api/repairs", "POST",
                    {"type": "water", "description": "", "phone": "138"},
                    r.status_code, body)
        f_checks.append(ok)

        ok = _check(
            "F2. body.msg 含「故障描述」",
            "故障描述" in msg,
            "包含「故障描述」",
            f"msg={msg!r}",
            "/api/repairs", "POST",
            {"type": "water", "description": "", "phone": "138"},
            r.status_code, body,
        )
        f_checks.append(ok)

        r = c.post("/api/repairs", headers=h_demo,
                   json={"type": "water", "description": "水管漏水", "phone": ""})
        body = r.get_json(silent=True) or {}
        msg = body.get("msg", "") or ""
        print(f"  F3. POST 空电话 -> HTTP {r.status_code}, msg={msg!r}")

        ok = _check("F3. HTTP 400", r.status_code == 400, 400, r.status_code,
                    "/api/repairs", "POST",
                    {"type": "water", "description": "水管漏水", "phone": ""},
                    r.status_code, body)
        f_checks.append(ok)

        ok = _check(
            "F3. body.msg 含「联系电话」",
            "联系电话" in msg,
            "包含「联系电话」",
            f"msg={msg!r}",
            "/api/repairs", "POST",
            {"type": "water", "description": "水管漏水", "phone": ""},
            r.status_code, body,
        )
        f_checks.append(ok)

        f4_body = {
            "type": "gas",
            "description": "厨房燃气灶点不着火",
            "phone": "13800001234",
            "urgency": "urgent",
        }
        r = c.post("/api/repairs", headers=h_demo, json=f4_body)
        body = r.get_json(silent=True) or {}
        repair_new = body.get("repair", {}) or {}
        repair_new_id = repair_new.get("id")
        print(f"  F4. POST 合法报修 -> HTTP {r.status_code}, id={repair_new_id}")
        print(f"      status={repair_new.get('status')}, urgency={repair_new.get('urgency')}, type={repair_new.get('type')}")

        ok = _check("F4. HTTP 201", r.status_code == 201, 201, r.status_code,
                    "/api/repairs", "POST", f4_body, r.status_code, body)
        f_checks.append(ok)

        ok = _check(
            "F4. repair.status == 'pending'",
            repair_new.get("status") == "pending",
            "pending",
            f"{repair_new.get('status')!r}",
            "/api/repairs", "POST", f4_body, r.status_code, body,
        )
        f_checks.append(ok)

        ok = _check(
            "F4. repair.urgency == 'urgent'",
            repair_new.get("urgency") == "urgent",
            "urgent",
            f"{repair_new.get('urgency')!r}",
            "/api/repairs", "POST", f4_body, r.status_code, body,
        )
        f_checks.append(ok)

        ok = _check(
            "F4. repair.type == 'gas'",
            repair_new.get("type") == "gas",
            "gas",
            f"{repair_new.get('type')!r}",
            "/api/repairs", "POST", f4_body, r.status_code, body,
        )
        f_checks.append(ok)

        r = c.get("/api/repairs", headers=h_demo)
        body = r.get_json(silent=True) or {}
        repairs_after = body.get("repairs", []) or []
        print(f"  F5. 再次 GET repairs -> count={len(repairs_after)} (之前 {len(repairs_before)})")

        ok = _check(
            f"F5. 长度相对 F1 之前 +1 ({len(repairs_before)} -> {len(repairs_after)})",
            len(repairs_after) == len(repairs_before) + 1,
            f"{len(repairs_before) + 1}",
            f"{len(repairs_after)}",
            "/api/repairs", "GET", None, r.status_code, body,
        )
        f_checks.append(ok)

        if repairs_after:
            newest = repairs_after[0]
            matches = (
                newest.get("type") == f4_body["type"]
                and newest.get("description") == f4_body["description"]
                and newest.get("phone") == f4_body["phone"]
                and newest.get("urgency") == f4_body["urgency"]
            )
            ok = _check(
                "F5. 最新一条与 F4 提交内容一致",
                matches,
                f"type={f4_body['type']}, desc={f4_body['description']}, "
                f"phone={f4_body['phone']}, urgency={f4_body['urgency']}",
                f"newest: type={newest.get('type')}, desc={newest.get('description')}, "
                f"phone={newest.get('phone')}, urgency={newest.get('urgency')}",
                "/api/repairs", "GET", None, r.status_code, body,
            )
            f_checks.append(ok)

        if repair_new_id:
            r = c.get(f"/api/repairs/{repair_new_id}", headers=h_demo)
            body = r.get_json(silent=True) or {}
            repair_detail = body.get("repair", {}) or {}
            print(f"  F6. GET /api/repairs/{repair_new_id} -> HTTP {r.status_code}")

            ok = _check("F6. HTTP 200", r.status_code == 200, 200, r.status_code,
                        f"/api/repairs/{repair_new_id}", "GET", None, r.status_code, body)
            f_checks.append(ok)

            matches_detail = (
                repair_detail.get("type") == f4_body["type"]
                and repair_detail.get("description") == f4_body["description"]
                and repair_detail.get("phone") == f4_body["phone"]
                and repair_detail.get("urgency") == f4_body["urgency"]
                and repair_detail.get("status") == "pending"
            )
            ok = _check(
                "F6. 详情字段与 F4 提交一致",
                matches_detail,
                f"type={f4_body['type']}, desc={f4_body['description']}, "
                f"phone={f4_body['phone']}, urgency={f4_body['urgency']}, status=pending",
                f"detail: {repair_detail}",
                f"/api/repairs/{repair_new_id}", "GET", None, r.status_code, body,
            )
            f_checks.append(ok)
        else:
            f_checks.append(False)
            f_checks.append(False)

        tr62_ok = len(f_checks) >= 3 and all(f_checks[:3])
        tr63_ok = len(f_checks) >= 7 and all(f_checks[3:7])
        tr64_ok = len(f_checks) >= 7 and all(f_checks[7:])
        TR6_RESULTS["TR-6.2"] = tr62_ok
        TR6_RESULTS["TR-6.3"] = tr63_ok
        TR6_RESULTS["TR-6.4"] = tr64_ok

        # ============================================================
        # Part G — 无 token 访问受保护接口 (Checkpoint 9-4)
        # ============================================================
        _print_section("Part G — 无 token 访问受保护接口 (Checkpoint 9-4)")
        g_checks = []

        r = c.get("/api/bills")
        body = r.get_json(silent=True) or {}
        print(f"  G1. 无 token GET /api/bills -> HTTP {r.status_code}")

        ok = _check(
            "G1. HTTP != 200 (应为 401/422)",
            r.status_code != 200,
            "非 200",
            f"{r.status_code}",
            "/api/bills", "GET", None, r.status_code, body,
        )
        g_checks.append(ok)

        r = c.get("/api/dashboard")
        body = r.get_json(silent=True) or {}
        print(f"  G2. 无 token GET /api/dashboard -> HTTP {r.status_code}")

        ok = _check(
            "G2. HTTP != 200 (应为 401/422)",
            r.status_code != 200,
            "非 200",
            f"{r.status_code}",
            "/api/dashboard", "GET", None, r.status_code, body,
        )
        g_checks.append(ok)

        r = c.get("/api/repairs")
        body = r.get_json(silent=True) or {}
        print(f"  G3. 无 token GET /api/repairs -> HTTP {r.status_code}")

        ok = _check(
            "G3. HTTP != 200 (应为 401/422)",
            r.status_code != 200,
            "非 200",
            f"{r.status_code}",
            "/api/repairs", "GET", None, r.status_code, body,
        )
        g_checks.append(ok)

        # ============================================================
        # 最终结论汇总
        # ============================================================
        _print_section("任务 5 — 四项结论")
        for k, v in TR5_RESULTS.items():
            status = "✅ 通过" if v else "❌ 未通过"
            print(f"  {k} : {status}")

        tr5_all = all(TR5_RESULTS.values())

        _print_section("任务 6 — 四项结论")
        for k, v in TR6_RESULTS.items():
            status = "✅ 通过" if v else "❌ 未通过"
            print(f"  {k} : {status}")

        tr6_all = all(TR6_RESULTS.values())

        _print_section("Part G — 无 token 防护")
        print(f"  G1 (bills 无 token)    : {'✅ PASS' if g_checks[0] else '❌ FAIL'}")
        print(f"  G2 (dashboard 无 token): {'✅ PASS' if g_checks[1] else '❌ FAIL'}")
        print(f"  G3 (repairs 无 token)  : {'✅ PASS' if g_checks[2] else '❌ FAIL'}")
        g_all = all(g_checks)
        print(f"  Checkpoint 9-4 整体    : {'✅ 通过' if g_all else '❌ 未通过'}")

        print("\n" + "-" * 70)
        print(f"  任务 5 整体 : {'✅ 全部通过' if tr5_all else '❌ 存在失败项'}")
        print(f"  任务 6 整体 : {'✅ 全部通过' if tr6_all else '❌ 存在失败项'}")
        print(f"  总体结果    : {'✅ 全部通过' if (tr5_all and tr6_all and g_all) else '❌ 存在失败项'}")
        print("-" * 70)

        if FAILURES:
            _print_section("失败断言详情 (期望值 vs 实际值)")
            for i, f in enumerate(FAILURES, 1):
                print(f"\n--- 失败 {i}: {f['name']} ---")
                if f.get("req_method") and f.get("req_url"):
                    print(f"  请求: {f['req_method']} {f['req_url']}")
                if f.get("req_body") is not None:
                    print(f"  请求 Body: {json.dumps(f['req_body'], ensure_ascii=False)}")
                print(f"  响应状态码: {f['resp_status']}")
                if f.get("resp_body") is not None:
                    rb = f["resp_body"]
                    if isinstance(rb, dict):
                        for k, v in rb.items():
                            if k == "msg":
                                print(f"  响应 msg: {v}")
                        else:
                            pass
                    print(f"  响应 Body: {json.dumps(rb, ensure_ascii=False) if isinstance(rb, (dict, list)) else repr(rb)}")
                if f.get("extra"):
                    print(f"  附加信息: {f['extra']}")

        return 0 if (tr5_all and tr6_all and g_all) else 1


if __name__ == "__main__":
    sys.exit(run())
