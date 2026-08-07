"""阶梯计费 calculate_tiered_amount 精确断言测试"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.billing import calculate_tiered_amount


def run_test(label, fn):
    try:
        result = fn()
        print(f"  [{label}] PASS")
        return True
    except AssertionError as e:
        print(f"  [{label}] FAIL: {e}")
        return False


def print_case_header(case_id, type_, usage, expected_amount):
    print(f"\n=== 用例 {case_id}: {type_} {usage} (期望金额 {expected_amount:.2f}) ===")


def main():
    app = create_app()
    all_passed = True

    with app.app_context():
        print("=" * 60)
        print("阶梯计费算法正确性验证测试")
        print("=" * 60)

        results = {}

        # ---- 用例 a: electricity 100 度 ----
        case_id = "a"
        type_, usage = "electricity", 100
        expected_amount = 58.80
        print_case_header(case_id, type_, usage, expected_amount)
        r = calculate_tiered_amount(type_, usage)
        actual_amount = round(r["amount"], 2)
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        ok = True

        def test_a():
            assert round(r["amount"], 2) == expected_amount, \
                f"amount 不匹配: 实际 {round(r['amount'], 2)}, 期望 {expected_amount}"
            assert len(r["breakdown"]) >= 1, \
                f"breakdown 长度不足: {len(r['breakdown'])} < 1"

        if not run_test("TR-4.1-amount+breakdown长度", test_a):
            ok = False
            all_passed = False
            print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 用例 b: electricity 250 度 ----
        case_id = "b"
        type_, usage = "electricity", 250
        expected_amount = 150.50
        print_case_header(case_id, type_, usage, expected_amount)
        r = calculate_tiered_amount(type_, usage)
        actual_amount = round(r["amount"], 2)
        subtotal_sum = sum(bd["subtotal"] for bd in r["breakdown"])
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        print(f"  breakdown 档数: {len(r['breakdown'])}  |  各档 subtotal 之和: {subtotal_sum:.2f}")
        ok = True

        def test_b_amount():
            assert round(r["amount"], 2) == expected_amount, \
                f"amount 不匹配: 实际 {round(r['amount'], 2)}, 期望 {expected_amount}"

        def test_b_breakdown_len():
            assert len(r["breakdown"]) >= 2, \
                f"breakdown 长度不足: {len(r['breakdown'])} < 2"

        def test_b_subtotal_sum():
            s = sum(bd["subtotal"] for bd in r["breakdown"])
            assert abs(s - expected_amount) <= 0.01, \
                f"subtotal 之和 {s:.2f} 与 amount {expected_amount:.2f} 差距超过 0.01"

        for name, fn in [
            ("TR-4.2.1-amount", test_b_amount),
            ("TR-4.2.2-breakdown长度>=2", test_b_breakdown_len),
            ("TR-4.2.3-subtotal之和=amount(容差0.01)", test_b_subtotal_sum),
        ]:
            if not run_test(name, fn):
                ok = False
                all_passed = False
                print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 用例 c: water 15 吨 ----
        case_id = "c"
        type_, usage = "water", 15
        expected_amount = 55.80
        print_case_header(case_id, type_, usage, expected_amount)
        r = calculate_tiered_amount(type_, usage)
        actual_amount = round(r["amount"], 2)
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        ok = True

        def test_c():
            assert round(r["amount"], 2) == expected_amount, \
                f"amount 不匹配: 实际 {round(r['amount'], 2)}, 期望 {expected_amount}"

        if not run_test("TR-4.3-water-amount", test_c):
            ok = False
            all_passed = False
            print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 用例 d: gas 45 立方 ----
        case_id = "d"
        type_, usage = "gas", 45
        expected_amount = 120.15
        print_case_header(case_id, type_, usage, expected_amount)
        r = calculate_tiered_amount(type_, usage)
        actual_amount = round(r["amount"], 2)
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        ok = True

        def test_d():
            assert round(r["amount"], 2) == expected_amount, \
                f"amount 不匹配: 实际 {round(r['amount'], 2)}, 期望 {expected_amount}"

        if not run_test("TR-4.4-gas-amount", test_d):
            ok = False
            all_passed = False
            print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 附加校验：各档 usage_in_tier 之和 == usage (a-d 再跑一遍) ----
        print("\n=== 附加校验: usage_in_tier 之和 == 传入 usage (容差 0.001) ===")
        extra_ok = True
        for label, type_, usage in [
            ("a", "electricity", 100),
            ("b", "electricity", 250),
            ("c", "water", 15),
            ("d", "gas", 45),
        ]:
            r = calculate_tiered_amount(type_, usage)
            s = sum(bd["usage_in_tier"] for bd in r["breakdown"])
            try:
                assert abs(s - usage) <= 0.001, \
                    f"用例{label}: usage_in_tier 之和 {s} != 传入 {usage}"
                print(f"  用例{label} ({type_} {usage}): sum={s}  PASS")
            except AssertionError as e:
                print(f"  用例{label} ({type_} {usage}): sum={s}  FAIL: {e}")
                print(f"    breakdown: {r['breakdown']}")
                extra_ok = False
                all_passed = False

        # ---- 用例 e: electricity 0 度 ----
        case_id = "e"
        type_, usage = "electricity", 0
        expected_amount = 0.0
        print_case_header(case_id, type_, usage, expected_amount)
        r = calculate_tiered_amount(type_, usage)
        actual_amount = r["amount"]
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        print(f"  breakdown 档数: {len(r['breakdown'])}")
        ok = True

        def test_e_amount():
            assert r["amount"] == 0.0, \
                f"amount 不匹配: 实际 {r['amount']}, 期望 0.0"

        def test_e_usage_zero():
            for bd in r["breakdown"]:
                assert bd["usage_in_tier"] == 0, \
                    f"tier {bd['tier']} usage_in_tier = {bd['usage_in_tier']} != 0"

        for name, fn in [
            ("e-amount==0", test_e_amount),
            ("e-各档usage_in_tier全0", test_e_usage_zero),
        ]:
            if not run_test(name, fn):
                ok = False
                all_passed = False
                print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 用例 f: electricity 1000 度（跨 3 档）----
        case_id = "f"
        type_, usage = "electricity", 1000
        expected_amount = 779.00
        print_case_header(case_id, type_, usage, expected_amount)
        print("  手工计算: 180×0.588 + 220×0.638 + 600×0.888")
        print(f"          = {180*0.588:.2f} + {220*0.638:.2f} + {600*0.888:.2f}")
        print(f"          = {180*0.588 + 220*0.638 + 600*0.888:.2f}")
        r = calculate_tiered_amount(type_, usage)
        actual_amount = r["amount"]
        print(f"  实际 amount: {actual_amount:.2f}  |  期望 amount: {expected_amount:.2f}")
        ok = True

        def test_f():
            assert r["amount"] == expected_amount, \
                f"amount 不匹配: 实际 {r['amount']}, 期望 {expected_amount}"

        if not run_test("f-跨3档精确金额=779.00", test_f):
            ok = False
            all_passed = False
            print(f"  完整 breakdown: {r['breakdown']}")

        results[case_id] = ok

        # ---- 汇总 ----
        print("\n" + "=" * 60)
        print("测试结论汇总")
        print("=" * 60)
        print("用例结果:")
        for cid in ["a", "b", "c", "d", "e", "f"]:
            status = "PASS" if results.get(cid) else "FAIL"
            print(f"  用例 {cid}: {status}")

        print("\nTR-4.1 ~ TR-4.4 结论:")
        print(f"  TR-4.1 (electricity 100度 amount+breakdown): {'通过' if results['a'] else '失败'}")
        print(f"  TR-4.2 (electricity 250度 amount+breakdown>=2+subtotal和): {'通过' if results['b'] else '失败'}")
        print(f"  TR-4.3 (water 15吨 amount): {'通过' if results['c'] else '失败'}")
        print(f"  TR-4.4 (gas 45立方 amount): {'通过' if results['d'] else '失败'}")
        print(f"  附加校验 (usage_in_tier 之和): {'通过' if extra_ok else '失败'}")

        print()
        if all_passed and extra_ok:
            print("🎉 阶梯计费算法正确性验证全部通过")
        else:
            failed = [cid for cid in ["a", "b", "c", "d", "e", "f"] if not results.get(cid)]
            if not extra_ok:
                failed.append("附加校验")
            print(f"❌ 存在失败用例: {', '.join(failed)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
