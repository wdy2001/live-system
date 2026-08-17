"""Task5 缴费功能验证脚本（通过 HTTP 接口）"""
import json
import sys
import requests

BASE_URL = "http://localhost:5000/api"

def login(username="demo", password="demo123"):
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.text}"
    return resp.json()["access_token"]


def get_bills(token, status=None, btype=None):
    params = {}
    if status:
        params["status"] = status
    if btype:
        params["type"] = btype
    resp = requests.get(
        f"{BASE_URL}/bills",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=10,
    )
    assert resp.status_code == 200, f"获取账单失败: {resp.status_code} {resp.text}"
    return resp.json()["bills"]


def get_bill_detail(token, bill_id):
    resp = requests.get(
        f"{BASE_URL}/bills/{bill_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    assert resp.status_code == 200, f"获取账单详情失败: {resp.status_code} {resp.text}"
    return resp.json()["bill"]


def pay_bill(token, bill_id, method="alipay"):
    resp = requests.post(
        f"{BASE_URL}/bills/{bill_id}/pay",
        headers={"Authorization": f"Bearer {token}"},
        json={"method": method},
        timeout=10,
    )
    return resp


def main():
    print("=" * 70)
    print("  Task5 验证脚本：电费/水费/燃气费缴费功能")
    print("=" * 70)

    token = login()
    print(f"\n✅ 登录成功 demo/demo123，TOKEN 获取完成")

    results = {}

    print("\n" + "=" * 70)
    print("  Checkpoint 5.1 ~ 5.4 验证（使用 electricity 类型账单）")
    print("=" * 70)

    # ====== 找一条 unpaid 的 electricity 账单 ======
    unpaid_electricity = get_bills(token, status="unpaid", btype="electricity")
    assert len(unpaid_electricity) > 0, "没有找到 unpaid electricity 账单"
    bill_id = unpaid_electricity[0]["id"]
    bill_before = unpaid_electricity[0]
    meter_id = bill_before["meter_id"]
    bill_amount = bill_before["amount"]
    bill_current_reading = bill_before["current_reading"]
    meter_reading_before = bill_before["meter"]["current_reading"]

    print(f"\n  选中账单 bill_id={bill_id}, type={bill_before['type']}, "
          f"amount={bill_amount}, meter_id={meter_id}")
    print(f"  支付前 meter.current_reading (A) = {meter_reading_before}")
    print(f"  bill.current_reading (B) = {bill_current_reading}")

    # ====== Checkpoint 5.1: 支付成功 ======
    print("\n--- Checkpoint 5.1: 支付成功 ---")
    resp = pay_bill(token, bill_id)
    cp51_passed = True
    cp51_detail = []

    if resp.status_code != 200:
        cp51_passed = False
        cp51_detail.append(f"HTTP 状态码: {resp.status_code} (期望 200)")
        try:
            cp51_detail.append(f"响应: {resp.json()}")
        except Exception:
            cp51_detail.append(f"响应: {resp.text}")
    else:
        data = resp.json()
        paid_bill = data.get("bill", {})
        payment = data.get("payment", {})

        if paid_bill.get("status") != "paid":
            cp51_passed = False
            cp51_detail.append(f"bill.status={paid_bill.get('status')} (期望 paid)")
        else:
            cp51_detail.append(f"bill.status={paid_bill.get('status')} ✓")

        transaction_no = payment.get("transaction_no", "")
        if not transaction_no.startswith("PAY"):
            cp51_passed = False
            cp51_detail.append(f"transaction_no={transaction_no} (期望以 PAY 开头)")
        else:
            cp51_detail.append(f"transaction_no={transaction_no} ✓")

        if abs(float(payment.get("amount", 0)) - float(bill_amount)) > 0.01:
            cp51_passed = False
            cp51_detail.append(
                f"payment.amount={payment.get('amount')} ≠ bill.amount={bill_amount}"
            )
        else:
            cp51_detail.append(
                f"payment.amount={payment.get('amount')} == bill.amount={bill_amount} ✓"
            )

    results["Checkpoint 5.1"] = {"passed": cp51_passed, "detail": cp51_detail}
    status_icon = "✅ PASS" if cp51_passed else "❌ FAIL"
    print(f"  {status_icon}: Checkpoint 5.1（支付成功）")
    for d in cp51_detail:
        print(f"    - {d}")

    # ====== Checkpoint 5.2: 重复支付拦截 ======
    print("\n--- Checkpoint 5.2: 重复支付拦截 ---")
    resp2 = pay_bill(token, bill_id)
    cp52_passed = True
    cp52_detail = []

    if resp2.status_code != 400:
        cp52_passed = False
        cp52_detail.append(f"HTTP 状态码: {resp2.status_code} (期望 400)")
    else:
        cp52_detail.append(f"HTTP 状态码: 400 ✓")

    try:
        msg = resp2.json().get("msg", "")
    except Exception:
        msg = resp2.text

    if "已支付" not in msg and "已缴" not in msg:
        cp52_passed = False
        cp52_detail.append(f"msg='{msg}' (期望包含'已支付'或'已缴')")
    else:
        cp52_detail.append(f"msg='{msg}' ✓")

    results["Checkpoint 5.2"] = {"passed": cp52_passed, "detail": cp52_detail}
    status_icon = "✅ PASS" if cp52_passed else "❌ FAIL"
    print(f"  {status_icon}: Checkpoint 5.2（重复支付拦截）")
    for d in cp52_detail:
        print(f"    - {d}")

    # ====== Checkpoint 5.3: 账单详情含阶梯拆分 ======
    print("\n--- Checkpoint 5.3: 账单详情含阶梯拆分+金额一致 ---")
    detail = get_bill_detail(token, bill_id)
    cp53_passed = True
    cp53_detail = []

    breakdown = detail.get("breakdown", [])
    if not isinstance(breakdown, list) or len(breakdown) < 1:
        cp53_passed = False
        cp53_detail.append(f"breakdown={breakdown} (期望数组且长度≥1)")
    else:
        cp53_detail.append(f"breakdown 是数组，长度={len(breakdown)} ✓")

    if isinstance(breakdown, list) and len(breakdown) >= 1:
        try:
            tier_amount_sum = sum(float(x.get("tier_amount", 0)) for x in breakdown)
        except KeyError as e:
            cp53_passed = False
            cp53_detail.append(f"breakdown 字段缺失 {e}，检查字段名")
            tier_amount_sum = -9999
        except Exception as e:
            cp53_passed = False
            cp53_detail.append(f"计算 tier_amount 求和出错: {e}")
            tier_amount_sum = -9999

        if tier_amount_sum >= 0:
            bill_amount_val = float(detail.get("amount", 0))
            diff = abs(tier_amount_sum - bill_amount_val)
            if diff > 0.01:
                cp53_passed = False
                cp53_detail.append(
                    f"sum(tier_amount)={tier_amount_sum} vs bill.amount={bill_amount_val}, "
                    f"差值={diff} (>0.01)"
                )
            else:
                cp53_detail.append(
                    f"sum(tier_amount)={tier_amount_sum} ≈ bill.amount={bill_amount_val}, "
                    f"差值={diff} ≤ 0.01 ✓"
                )

    results["Checkpoint 5.3"] = {"passed": cp53_passed, "detail": cp53_detail}
    status_icon = "✅ PASS" if cp53_passed else "❌ FAIL"
    print(f"  {status_icon}: Checkpoint 5.3（阶梯拆分+金额一致）")
    for d in cp53_detail:
        print(f"    - {d}")

    # ====== Checkpoint 5.4: 表计读数同步 ======
    print("\n--- Checkpoint 5.4: 表计读数同步 ---")
    detail2 = get_bill_detail(token, bill_id)
    meter_obj = detail2.get("meter", {})
    cp54_passed = True
    cp54_detail = []

    meter_current = float(meter_obj.get("current_reading", -9999))
    bill_current = float(detail2.get("current_reading", -9999))

    if abs(meter_current - bill_current) > 0.01:
        cp54_passed = False
        cp54_detail.append(
            f"meter.current_reading={meter_current} ≠ bill.current_reading={bill_current}"
        )
    else:
        cp54_detail.append(
            f"meter.current_reading={meter_current} == bill.current_reading={bill_current} ✓"
        )
        cp54_detail.append(
            f"  (支付前 meter A={meter_reading_before}, bill B={bill_current_reading}, "
            f"支付后 meter 已更新为 B)"
        )

    results["Checkpoint 5.4"] = {"passed": cp54_passed, "detail": cp54_detail}
    status_icon = "✅ PASS" if cp54_passed else "❌ FAIL"
    print(f"  {status_icon}: Checkpoint 5.4（表计读数同步）")
    for d in cp54_detail:
        print(f"    - {d}")

    # ====== Checkpoint 5.5 / TR-5: 三种类型各测1条 ======
    print("\n" + "=" * 70)
    print("  Checkpoint 5.5 / TR-5: 三种类型（电/水/气）支付测试")
    print("=" * 70)

    type_results = {}
    for btype in ["electricity", "water", "gas"]:
        print(f"\n--- 类型: {btype} ---")
        unpaid = get_bills(token, status="unpaid", btype=btype)
        if len(unpaid) == 0:
            print(f"  ⚠️  没有 unpaid 的 {btype} 账单，跳过该类型")
            type_results[btype] = {"passed": False, "detail": "无 unpaid 账单"}
            continue

        test_bill = unpaid[0]
        tid = test_bill["id"]
        print(f"  选中 bill_id={tid}, amount={test_bill['amount']}")

        r = pay_bill(token, tid)
        if r.status_code != 200:
            type_results[btype] = {
                "passed": False,
                "detail": f"HTTP {r.status_code}: {r.text[:200]}",
            }
            print(f"  ❌ FAIL: HTTP {r.status_code}")
            continue

        d = r.json()
        ok_status = d.get("bill", {}).get("status") == "paid"
        ok_txn = d.get("payment", {}).get("transaction_no", "").startswith("PAY")
        ok_amount = (
            abs(
                float(d.get("payment", {}).get("amount", 0))
                - float(test_bill["amount"])
            )
            <= 0.01
        )

        passed = ok_status and ok_txn and ok_amount
        type_results[btype] = {
            "passed": passed,
            "detail": f"status={ok_status}, txn_prefix={ok_txn}, amount={ok_amount}",
        }
        icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {icon}")
        print(f"    bill.status={d.get('bill', {}).get('status')}, "
              f"txn={d.get('payment', {}).get('transaction_no')}, "
              f"amount={d.get('payment', {}).get('amount')}")

    results["Checkpoint 5.5 (三类支付)"] = {
        "passed": all(v["passed"] for v in type_results.values()),
        "detail": [f"{k}: {'PASS' if v['passed'] else 'FAIL'} - {v['detail']}"
                   for k, v in type_results.items()],
    }

    # ====== 汇总 ======
    print("\n" + "=" * 70)
    print("  Task5 验证结果汇总")
    print("=" * 70)
    all_passed = True
    for name, info in results.items():
        icon = "✅" if info["passed"] else "❌"
        print(f"{icon} {name}")
        for d in info["detail"]:
            print(f"     {d}")
        if not info["passed"]:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 Task5 全部通过！")
        print("=" * 70)
        sys.exit(0)
    else:
        print("  💥 Task5 存在失败项，请检查修复！")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
