"""前后端联调 Smoke 测试脚本 - 典型用户主流程
用法: USE_SQLITE=true python test_flow.py
"""
import os
import sys
import json

os.environ.setdefault("USE_SQLITE", "true")

from app import create_app
from extensions import db
from seed import seed


PASS = 0
FAIL = 0
FAILURES = []


def check(name, condition, extra=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ PASS: {name}")
    else:
        FAIL += 1
        msg = f"  ✗ FAIL: {name}"
        if extra:
            msg += f" | {extra}"
        print(msg)
        FAILURES.append(name)


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def json_of(resp):
    try:
        return resp.get_json()
    except Exception:
        try:
            return json.loads(resp.data.decode("utf-8"))
        except Exception:
            return {"_raw": resp.data[:500]}


def main():
    app = create_app()
    with app.app_context():
        db.drop_all()
        seed()
    client = app.test_client()

    print("\n" + "=" * 60)
    print("  前后端联调 SMOKE 测试 - 典型用户主流程")
    print("=" * 60)

    demo_token = None

    # ======================================================================
    # Step 1: 用 demo/demo123 登录获取 token
    # ======================================================================
    print("\n[Step 1] 登录 POST /api/auth/login")
    r = client.post("/api/auth/login", json={
        "username": "demo",
        "password": "demo123",
    })
    data = json_of(r)
    check("登录状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    check("登录返回 token", "token" in data and bool(data["token"]),
          f"body keys={list(data.keys())}")
    demo_token = data.get("token") if r.status_code == 200 else None
    check("demo_token 非空", bool(demo_token))

    # ======================================================================
    # Step 2: 取 /dashboard 结果保存 unpaid_total / unpaid_count
    # ======================================================================
    print("\n[Step 2] 初始 Dashboard GET /api/dashboard")
    r = client.get("/api/dashboard", headers=auth_header(demo_token))
    data = json_of(r)
    check("dashboard 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    initial_unpaid_total = data.get("unpaid_total") if isinstance(data, dict) else None
    initial_unpaid_count = data.get("unpaid_count") if isinstance(data, dict) else None
    check("unpaid_total 是数字", isinstance(initial_unpaid_total, (int, float)),
          f"unpaid_total={initial_unpaid_total}")
    check("unpaid_count 是数字", isinstance(initial_unpaid_count, (int, float)),
          f"unpaid_count={initial_unpaid_count}")
    check("初始 unpaid_count > 0", initial_unpaid_count > 0,
          f"unpaid_count={initial_unpaid_count}")
    print(f"    初始: unpaid_total={initial_unpaid_total}, unpaid_count={initial_unpaid_count}")

    # ======================================================================
    # Step 3: 取 /bills?status=unpaid 得到第一笔 unpaid bill
    # ======================================================================
    print("\n[Step 3] 未缴账单列表 GET /api/bills?status=unpaid")
    r = client.get("/api/bills?status=unpaid", headers=auth_header(demo_token))
    data = json_of(r)
    check("bills?status=unpaid 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    unpaid_bills = data.get("bills", []) if isinstance(data, dict) else []
    check("unpaid bills 非空", len(unpaid_bills) > 0,
          f"len={len(unpaid_bills)}")
    first_unpaid = unpaid_bills[0] if unpaid_bills else None
    check("第一笔 unpaid bill 存在", first_unpaid is not None)
    first_bill_id = first_unpaid.get("id") if first_unpaid else None
    first_bill_amount = first_unpaid.get("amount") if first_unpaid else None
    check("bill 有 id", first_bill_id is not None, f"first_unpaid={first_unpaid}")
    check("bill 有 amount", isinstance(first_bill_amount, (int, float)),
          f"amount={first_bill_amount}")
    print(f"    第一笔未缴: bill_id={first_bill_id}, amount={first_bill_amount}")

    # ======================================================================
    # Step 4: 支付该 bill，再次 /dashboard 验证 unpaid_count 减少 1 且 unpaid_total 相应减少
    # ======================================================================
    print(f"\n[Step 4] 支付 bill_id={first_bill_id} POST /api/bills/{first_bill_id}/pay")
    r = client.post(f"/api/bills/{first_bill_id}/pay",
                    headers=auth_header(demo_token), json={"method": "alipay"})
    data = json_of(r)
    check("支付状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    paid_bill_back = data.get("bill", {}) if isinstance(data, dict) else {}
    check("支付后 bill.status=paid", paid_bill_back.get("status") == "paid",
          f"bill_back={paid_bill_back}")
    check("支付返回 transaction_no", bool(data.get("transaction_no")) if isinstance(data, dict) else False,
          f"data={data}")

    print("\n  支付后再次查 Dashboard:")
    r2 = client.get("/api/dashboard", headers=auth_header(demo_token))
    data2 = json_of(r2)
    after_unpaid_total = data2.get("unpaid_total") if isinstance(data2, dict) else None
    after_unpaid_count = data2.get("unpaid_count") if isinstance(data2, dict) else None
    check("支付后 dashboard 状态码 200", r2.status_code == 200,
          f"got {r2.status_code}, body={data2}")
    expected_count = initial_unpaid_count - 1
    check(f"unpaid_count 减少 1 ({initial_unpaid_count} -> {expected_count})",
          after_unpaid_count == expected_count,
          f"after={after_unpaid_count}, expected={expected_count}")
    expected_total_min = initial_unpaid_total - first_bill_amount - 0.02
    expected_total_max = initial_unpaid_total - first_bill_amount + 0.02
    check(f"unpaid_total 减少约 {first_bill_amount}",
          (after_unpaid_total is not None
           and expected_total_min <= after_unpaid_total <= expected_total_max),
          f"initial={initial_unpaid_total}, after={after_unpaid_total}, "
          f"bill_amount={first_bill_amount}, diff={initial_unpaid_total - after_unpaid_total if initial_unpaid_total is not None and after_unpaid_total is not None else 'N/A'}")
    print(f"    支付后: unpaid_total={after_unpaid_total}, unpaid_count={after_unpaid_count}")

    # ======================================================================
    # Step 5: 取 /bills?status=paid 检查新支付的账单已在列表
    # ======================================================================
    print("\n[Step 5] 已缴账单列表 GET /api/bills?status=paid")
    r = client.get("/api/bills?status=paid", headers=auth_header(demo_token))
    data = json_of(r)
    check("bills?status=paid 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    paid_bills = data.get("bills", []) if isinstance(data, dict) else []
    paid_bill_ids = [b.get("id") for b in paid_bills]
    check(f"新支付 bill_id={first_bill_id} 在已缴列表",
          first_bill_id in paid_bill_ids,
          f"paid_bill_ids={paid_bill_ids}, expected id={first_bill_id}")
    check("paid bills 数量 > 0", len(paid_bills) > 0,
          f"len={len(paid_bills)}")

    # ======================================================================
    # Step 6: 创建一条新报修：POST /repairs 合法参数
    # ======================================================================
    print("\n[Step 6] 创建报修 POST /api/repairs")
    new_repair_payload = {
        "type": "water",
        "description": "卫生间淋浴水龙头漏水，关不严，需要紧急维修",
        "phone": "13900001111",
        "urgency": "urgent",
    }
    r = client.post("/api/repairs", json=new_repair_payload,
                    headers=auth_header(demo_token))
    data = json_of(r)
    check("创建报修 状态码 201", r.status_code == 201,
          f"got {r.status_code}, body={data}")
    new_repair = data.get("repair", {}) if isinstance(data, dict) else {}
    new_repair_id = new_repair.get("id")
    check("新报修返回 id", new_repair_id is not None, f"repair={new_repair}")
    check("新报修 status=pending", new_repair.get("status") == "pending",
          f"repair={new_repair}")
    check("新报修 type=water", new_repair.get("type") == "water",
          f"repair={new_repair}")
    check("新报修 urgency=urgent", new_repair.get("urgency") == "urgent",
          f"repair={new_repair}")
    print(f"    新报修: repair_id={new_repair_id}, type=water, urgency=urgent")

    # ======================================================================
    # Step 7: 取 /repairs 列表验证新工单在第一条
    # ======================================================================
    print("\n[Step 7] 报修列表 GET /api/repairs 验证新工单在第一条")
    r = client.get("/api/repairs", headers=auth_header(demo_token))
    data = json_of(r)
    check("repairs 列表状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    repairs_list = data.get("repairs", []) if isinstance(data, dict) else []
    check("repairs 列表非空", len(repairs_list) > 0, f"len={len(repairs_list)}")
    first_repair = repairs_list[0] if repairs_list else None
    check("第一条 repair 是新创建的",
          first_repair is not None and first_repair.get("id") == new_repair_id,
          f"first_repair_id={first_repair.get('id') if first_repair else None}, expected={new_repair_id}")
    check("第一条 repair description 匹配",
          first_repair is not None and first_repair.get("description") == new_repair_payload["description"],
          f"description={first_repair.get('description') if first_repair else None}")

    # ======================================================================
    # Step 8: 取 /rules 验证长度 8，/households/mine 验证 3 meters
    # ======================================================================
    print("\n[Step 8a] 计费规则 GET /api/rules 验证长度 8")
    r = client.get("/api/rules")
    data = json_of(r)
    check("rules 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    rules = data.get("rules", []) if isinstance(data, dict) else []
    check("rules 长度为 8 (电3+水2+气3)", len(rules) == 8,
          f"len={len(rules)}")
    types_count = {}
    for rule in rules:
        t = rule.get("type")
        types_count[t] = types_count.get(t, 0) + 1
    check("rules: electricity=3", types_count.get("electricity") == 3, f"counts={types_count}")
    check("rules: water=2", types_count.get("water") == 2, f"counts={types_count}")
    check("rules: gas=3", types_count.get("gas") == 3, f"counts={types_count}")

    print("\n[Step 8b] 户号信息 GET /api/households/mine 验证 3 meters")
    r = client.get("/api/households/mine", headers=auth_header(demo_token))
    data = json_of(r)
    check("households/mine 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    households = data.get("households", []) if isinstance(data, dict) else []
    check("households 至少 1 户", len(households) >= 1, f"len={len(households)}")
    if households:
        h = households[0]
        meters = h.get("meters", [])
        check("household[0] 有 3 个 meters", len(meters) == 3,
              f"len={len(meters)}, meters={meters}")
        meter_types = {m.get("type") for m in meters}
        check("meters 覆盖 electricity/water/gas",
              meter_types == {"electricity", "water", "gas"},
              f"types={meter_types}")

    # ======================================================================
    # 汇总
    # ======================================================================
    print("\n" + "=" * 60)
    print(f"  SUMMARY: PASS={PASS} / FAIL={FAIL}")
    print("=" * 60)
    if FAILURES:
        print("  失败用例:")
        for idx, f in enumerate(FAILURES, 1):
            print(f"    {idx}. {f}")
    else:
        print("  ✅ 所有断言全部通过！")
    print()
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
