"""Task 5 测试脚本：账单查询/详情/支付 API 验证"""
import os
import sys
import json

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from models import Bill, Payment, User

app = create_app("development")
client = app.test_client()

PASSED = 0
FAILED = 0


def assert_true(cond, msg):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✅ PASS: {msg}")
    else:
        FAILED += 1
        print(f"  ❌ FAIL: {msg}")


def assert_equal(actual, expected, msg):
    assert_true(actual == expected, f"{msg} (expected={expected}, actual={actual})")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def login(username, password):
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    data = resp.get_json()
    return data["token"]


def register(username, password):
    resp = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "confirm_password": password,
            "real_name": "Test User",
            "phone": "13800000000",
        },
    )
    data = resp.get_json()
    return data.get("token")


def test_tr_5_1():
    """TR-5.1 筛选分页"""
    print("\n=== TR-5.1 筛选分页 ===")
    token = login("demo", "demo123")
    headers = auth_header(token)

    print("\n  Test 1: GET /api/bills?type=electricity&status=unpaid&page=1&per_page=10")
    resp = client.get(
        "/api/bills?type=electricity&status=unpaid&page=1&per_page=10",
        headers=headers,
    )
    assert_equal(resp.status_code, 200, "HTTP 200")
    data = resp.get_json()

    bills = data.get("bills", [])
    assert_true("bills" in data, "响应包含 bills 字段")
    assert_true("total" in data, "响应包含 total 字段")
    assert_true("page" in data, "响应包含 page 字段")
    assert_true("per_page" in data, "响应包含 per_page 字段")

    for b in bills:
        assert_equal(b["type"], "electricity", f"bill {b['id']} type == electricity")
        assert_equal(b["status"], "unpaid", f"bill {b['id']} status == unpaid")

    assert_equal(data["total"], 2, "total == 2 (2026-04 和 2026-05 两笔电费未缴)")
    assert_equal(data["page"], 1, "page == 1")
    assert_equal(data["per_page"], 10, "per_page == 10")

    print("\n  Test 2: GET /api/bills?status=paid (paid 账单数量 = 12)")
    resp = client.get("/api/bills?status=paid", headers=headers)
    assert_equal(resp.status_code, 200, "HTTP 200")
    data = resp.get_json()
    paid_count = data["total"]
    assert_equal(paid_count, 12, f"paid 账单数量 == 12 (period < '2026-04' = 4期 × 3类 = 12)")

    for b in data["bills"]:
        assert_equal(b["status"], "paid", f"bill {b['id']} status == paid")


def test_tr_5_2():
    """TR-5.2 账单详情 + 阶梯拆分"""
    print("\n=== TR-5.2 账单详情 + 阶梯拆分 ===")
    token = login("demo", "demo123")
    headers = auth_header(token)

    print("\n  Test 1: 找一条有跨阶梯 usage 的账单（优先 unpaid，否则找 paid）")
    candidate_bill = None

    resp = client.get(
        "/api/bills?status=unpaid&page=1&per_page=50",
        headers=headers,
    )
    unpaid_bills = resp.get_json()["bills"]
    for b in unpaid_bills:
        if (b["type"] == "water" and b["usage_amount"] > 12) or \
           (b["type"] == "electricity" and b["usage_amount"] > 180) or \
           (b["type"] == "gas" and b["usage_amount"] > 310):
            candidate_bill = b
            break

    if candidate_bill is None:
        print("    unpaid 中没有跨阶梯，从 paid 中找...")
        resp = client.get(
            "/api/bills?status=paid&page=1&per_page=50",
            headers=headers,
        )
        paid_bills = resp.get_json()["bills"]
        for b in paid_bills:
            if (b["type"] == "water" and b["usage_amount"] > 12) or \
               (b["type"] == "electricity" and b["usage_amount"] > 180) or \
               (b["type"] == "gas" and b["usage_amount"] > 310):
                candidate_bill = b
                break

    assert_true(candidate_bill is not None, "找到跨阶梯使用量的账单")
    bill_id = candidate_bill["id"]
    print(f"    使用 bill_id = {bill_id}, type = {candidate_bill['type']}, period = {candidate_bill['period']}, usage = {candidate_bill['usage_amount']}")

    resp = client.get(f"/api/bills/{bill_id}", headers=headers)
    assert_equal(resp.status_code, 200, "GET /api/bills/:id => 200")
    detail = resp.get_json()["bill"]

    assert_true("breakdown" in detail, "breakdown 字段存在")
    breakdown = detail["breakdown"]
    assert_true(len(breakdown) >= 2, f"breakdown 长度 >= 2 (实际={len(breakdown)})")
    for i, item in enumerate(breakdown):
        print(f"    tier {i+1}: tier={item['tier']}, usage_in_tier={item['usage_in_tier']}, subtotal={item['subtotal']}, description={item['description']}")

    subtotal_sum = sum(item["subtotal"] for item in breakdown)
    bill_amount = detail["amount"]
    diff = abs(subtotal_sum - bill_amount)
    assert_true(
        diff < 0.02,
        f"breakdown subtotal 之和与 bill.amount 差值 < 0.02 (sum={subtotal_sum:.2f}, amount={bill_amount:.2f}, diff={diff:.4f})"
    )

    assert_true("meter" in detail, "meter 字段存在")
    assert_true("household" in detail, "household 字段存在")
    assert_true("meter_no" in detail["meter"], "meter.meter_no 可访问")
    assert_true("household_no" in detail["household"], "household.household_no 可访问")
    print(f"    meter_no = {detail['meter']['meter_no']}, household_no = {detail['household']['household_no']}")

    print("\n  Test 2: 越权访问 - 注册新用户 userB，尝试访问 demo 的 bill_id")
    userb_token = register("userB_test_task5_v2", "test123456")
    userb_headers = auth_header(userb_token)
    resp = client.get(f"/api/bills/{bill_id}", headers=userb_headers)
    assert_equal(resp.status_code, 403, "越权访问返回 403")
    err_msg = resp.get_json().get("msg", "")
    assert_equal(err_msg, "无权访问该账单", f'错误消息为 "无权访问该账单" (实际="{err_msg}")')


def test_tr_5_3():
    """TR-5.3 支付幂等"""
    print("\n=== TR-5.3 支付幂等 ===")
    token = login("demo", "demo123")
    headers = auth_header(token)

    print("\n  先找一条 unpaid water bill (支付后不影响电费的测试)")
    resp = client.get(
        "/api/bills?type=water&status=unpaid&page=1&per_page=10",
        headers=headers,
    )
    data = resp.get_json()
    unpaid_water_bills = data["bills"]
    assert_true(len(unpaid_water_bills) > 0, "存在 unpaid water bill")

    test_bill = unpaid_water_bills[0]
    bill_id = test_bill["id"]
    print(f"    使用 bill_id = {bill_id}, period = {test_bill['period']}")

    print(f"\n  Test 1: 第 1 次 POST /api/bills/{bill_id}/pay => 200")
    resp = client.post(f"/api/bills/{bill_id}/pay", headers=headers, json={"method": "alipay"})
    assert_equal(resp.status_code, 200, "第 1 次支付 => 200")
    data1 = resp.get_json()
    assert_equal(data1["bill"]["status"], "paid", "bill.status = paid")
    assert_true("payment" in data1, "响应包含 payment 对象")

    print(f"\n  Test 2: 第 2 次 POST /api/bills/{bill_id}/pay => 400")
    resp = client.post(f"/api/bills/{bill_id}/pay", headers=headers, json={"method": "alipay"})
    assert_equal(resp.status_code, 400, "第 2 次支付 => 400")
    err_msg = resp.get_json().get("msg", "")
    assert_equal(err_msg, "该账单已支付", f'错误消息为 "该账单已支付" (实际="{err_msg}")')


def test_tr_5_4():
    """TR-5.4 支付记录正确性"""
    print("\n=== TR-5.4 支付记录正确性 ===")
    token = login("demo", "demo123")
    headers = auth_header(token)

    print("\n  先找一条 unpaid gas bill 用于支付测试")
    resp = client.get(
        "/api/bills?type=gas&status=unpaid&page=1&per_page=10",
        headers=headers,
    )
    data = resp.get_json()
    unpaid_gas_bills = data["bills"]
    assert_true(len(unpaid_gas_bills) > 0, "存在 unpaid gas bill")

    test_bill1 = unpaid_gas_bills[0]
    bill_id1 = test_bill1["id"]
    print(f"    Bill 1: bill_id = {bill_id1}, period = {test_bill1['period']}")

    print(f"\n  Test 1: 支付 bill_id={bill_id1}，验证支付记录")
    resp = client.post(f"/api/bills/{bill_id1}/pay", headers=headers, json={"method": "wechat"})
    assert_equal(resp.status_code, 200, "支付成功 => 200")
    pay_data = resp.get_json()
    bill = pay_data["bill"]
    payment = pay_data["payment"]

    assert_equal(bill["status"], "paid", "bill.status = 'paid'")
    assert_true(bill["paid_at"] is not None, "bill.paid_at != None")
    print(f"    bill.paid_at = {bill['paid_at']}")

    txn_no = payment["transaction_no"]
    assert_true(txn_no.startswith("PAY"), f"transaction_no 以 'PAY' 开头 (实际={txn_no[:10]}...)")
    assert_true(len(txn_no) >= 32, f"transaction_no 长度 >= 32 (实际={len(txn_no)})")
    print(f"    transaction_no = {txn_no} (len={len(txn_no)})")

    print("\n  找另一条 unpaid electricity bill 支付，验证唯一性")
    resp = client.get(
        "/api/bills?type=electricity&status=unpaid&page=1&per_page=10",
        headers=headers,
    )
    data = resp.get_json()
    unpaid_elec_bills = data["bills"]
    assert_true(len(unpaid_elec_bills) > 0, "仍存在 unpaid electricity bill")

    test_bill2 = unpaid_elec_bills[0]
    bill_id2 = test_bill2["id"]
    print(f"    Bill 2: bill_id = {bill_id2}, period = {test_bill2['period']}")

    resp = client.post(f"/api/bills/{bill_id2}/pay", headers=headers, json={"method": "alipay"})
    assert_equal(resp.status_code, 200, "Bill 2 支付成功 => 200")
    pay_data2 = resp.get_json()
    payment2 = pay_data2["payment"]
    txn_no2 = payment2["transaction_no"]

    assert_true(
        txn_no != txn_no2,
        f"两条不同支付的 transaction_no 互不相同 (tx1={txn_no[:15]}..., tx2={txn_no2[:15]}...)"
    )
    print(f"    transaction_no 2 = {txn_no2} (len={len(txn_no2)})")


def main():
    with app.app_context():
        from seed import seed as run_seed
        run_seed()

    print("\n" + "=" * 60)
    print("  Task 5 验证测试开始")
    print("=" * 60)

    test_tr_5_1()
    test_tr_5_2()
    test_tr_5_3()
    test_tr_5_4()

    print("\n" + "=" * 60)
    print(f"  测试结果: {PASSED} 通过, {FAILED} 失败")
    print("=" * 60)

    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
