"""TR-11.1 阶梯边界算法验证"""
import os
import sys

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.billing import calculate_tiered_amount

PASSED = 0
FAILED = 0

def check(cond, name, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✅ PASS: {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  ❌ FAIL: {name}" + (f"  ({detail})" if detail else ""))

app = create_app("development")

with app.app_context():
    print("\n=== TR-11.1 阶梯边界算法验证 ===\n")

    # Test 1: usage=0
    print("--- Test 1: 电 usage=0 ---")
    r1 = calculate_tiered_amount("electricity", 0)
    check(r1["amount"] == 0.0, f"amount=0", f"actual={r1['amount']}")
    all_zero = all(b["usage_in_tier"] == 0 for b in r1["breakdown"])
    check(all_zero, f"每档 usage_in_tier=0", f"actual={[b['usage_in_tier'] for b in r1['breakdown']]}")

    # Test 2: usage=179.99
    print("\n--- Test 2: 电 usage=179.99 ---")
    r2 = calculate_tiered_amount("electricity", 179.99)
    expected2 = round(179.99 * 0.588, 2)
    check(r2["amount"] == expected2, f"amount={expected2}", f"actual={r2['amount']}")
    t1_usage = r2["breakdown"][0]["usage_in_tier"]
    check(abs(t1_usage - 179.99) < 0.001, f"第1档 usage_in_tier=179.99", f"actual={t1_usage}")

    # Test 3: usage=180
    print("\n--- Test 3: 电 usage=180 ---")
    r3 = calculate_tiered_amount("electricity", 180)
    expected3 = round(180 * 0.588, 2)  # 105.84
    check(r3["amount"] == expected3, f"amount={expected3}", f"actual={r3['amount']}")
    check(abs(r3["breakdown"][0]["usage_in_tier"] - 180) < 0.001,
          f"仅第1档 usage_in_tier=180",
          f"actual={r3['breakdown'][0]['usage_in_tier']}")
    check(r3["breakdown"][1]["usage_in_tier"] == 0 and r3["breakdown"][2]["usage_in_tier"] == 0,
          "第2/3档 usage_in_tier=0")

    # Test 4: usage=180.01
    print("\n--- Test 4: 电 usage=180.01 ---")
    r4 = calculate_tiered_amount("electricity", 180.01)
    calc = 180 * 0.588 + 0.01 * 0.638  # 105.84 + 0.00638 = 105.84638 -> 四舍五入 105.85
    expected4 = round(calc, 2)
    check(r4["amount"] == expected4, f"amount≈{expected4}", f"actual={r4['amount']}, calc_raw={calc}")

    # Test 5: usage=100000 (超大值)
    print("\n--- Test 5: 电 usage=100000 (超大值) ---")
    try:
        r5 = calculate_tiered_amount("electricity", 100000)
        tier1_usage = r5["breakdown"][0]["usage_in_tier"]  # 180
        tier2_usage = r5["breakdown"][1]["usage_in_tier"]  # 220 (400-180)
        tier3_usage = r5["breakdown"][2]["usage_in_tier"]  # 99600 (100000 - 400)
        expected_t3 = 100000 - 400  # 99600
        check(abs(tier1_usage - 180) < 0.001, f"第1档=180", f"actual={tier1_usage}")
        check(abs(tier2_usage - 220) < 0.001, f"第2档=220", f"actual={tier2_usage}")
        check(abs(tier3_usage - expected_t3) < 0.001, f"第3档={expected_t3}", f"actual={tier3_usage}")
        expected_t3_amount = round(expected_t3 * 0.888, 2)
        actual_t3_subtotal = r5["breakdown"][2]["subtotal"]
        check(abs(actual_t3_subtotal - expected_t3_amount) < 0.02,
              f"第3档计费正确 ({expected_t3}×0.888≈{expected_t3_amount})",
              f"actual={actual_t3_subtotal}")
        print(f"  超大值测试: amount={r5['amount']}, 无异常")
    except Exception as e:
        check(False, f"超大值测试不报错", f"异常: {e}")

print(f"\n=== TR-11.1 结果: {PASSED} 通过, {FAILED} 失败 ===")
sys.exit(0 if FAILED == 0 else 1)
