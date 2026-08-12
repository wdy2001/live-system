"""阶梯计费核心服务测试脚本 - Task 2"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal, ROUND_HALF_UP
from app import create_app
from services.billing import calculate_tiered_amount


def print_breakdown(breakdown):
    """打印阶梯明细"""
    for item in breakdown:
        max_str = f"{item['max_usage']}" if item['max_usage'] is not None else "∞"
        print(f"  档{item['tier']}: {item['usage_in_tier']:.2f}单位 "
              f"[{item['min_usage']}-{max_str}] "
              f"@ {item['unit_price']:.4f} = {item['subtotal']:.2f}")


def verify_sum(result):
    """验证 breakdown subtotal 加总 = amount"""
    breakdown_sum = sum(Decimal(str(b['subtotal'])) for b in result['breakdown'])
    breakdown_sum_rounded = float(breakdown_sum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return breakdown_sum_rounded == result['amount'], breakdown_sum_rounded


def run_tests():
    app = create_app()
    results = {}
    
    with app.app_context():
        print("=" * 70)
        print("生活缴费系统 Task 2 - 阶梯计费核心服务验证")
        print("=" * 70)
        print()
        
        # ============================================================
        # TR-2.1: electricity 250 度
        # ============================================================
        print("-" * 70)
        print("TR-2.1: electricity 250 度")
        print("预期: amount=150.50, tier1=180度@0.588=105.84, tier2=70度@0.638=44.66")
        print("-" * 70)
        result = calculate_tiered_amount("electricity", 250)
        print(f"  返回 amount = {result['amount']:.2f}")
        print_breakdown(result['breakdown'])
        sum_ok, sum_val = verify_sum(result)
        print(f"  breakdown 加总验证: {sum_val:.2f} {'=' if sum_ok else '≠'} {result['amount']:.2f} -> {'PASS' if sum_ok else 'FAIL'}")
        
        # 详细检查
        tr21_ok = True
        tr21_detail = []
        if result['amount'] != 150.50:
            tr21_ok = False
            tr21_detail.append(f"amount 错误: 预期 150.50, 实际 {result['amount']:.2f}")
        
        # 检查 tier1
        tier1 = next((b for b in result['breakdown'] if b['tier'] == 1), None)
        if tier1 is None:
            tr21_ok = False
            tr21_detail.append("缺少 tier1")
        else:
            if abs(tier1['usage_in_tier'] - 180) > 0.001:
                tr21_ok = False
                tr21_detail.append(f"tier1 用量错误: 预期 180, 实际 {tier1['usage_in_tier']}")
            if abs(tier1['subtotal'] - 105.84) > 0.001:
                tr21_ok = False
                tr21_detail.append(f"tier1 subtotal 错误: 预期 105.84, 实际 {tier1['subtotal']:.2f}")
            if abs(tier1['unit_price'] - 0.588) > 0.0001:
                tr21_ok = False
                tr21_detail.append(f"tier1 单价错误: 预期 0.588, 实际 {tier1['unit_price']}")
        
        # 检查 tier2
        tier2 = next((b for b in result['breakdown'] if b['tier'] == 2), None)
        if tier2 is None:
            tr21_ok = False
            tr21_detail.append("缺少 tier2")
        else:
            if abs(tier2['usage_in_tier'] - 70) > 0.001:
                tr21_ok = False
                tr21_detail.append(f"tier2 用量错误: 预期 70, 实际 {tier2['usage_in_tier']}")
            if abs(tier2['subtotal'] - 44.66) > 0.001:
                tr21_ok = False
                tr21_detail.append(f"tier2 subtotal 错误: 预期 44.66, 实际 {tier2['subtotal']:.2f}")
            if abs(tier2['unit_price'] - 0.638) > 0.0001:
                tr21_ok = False
                tr21_detail.append(f"tier2 单价错误: 预期 0.638, 实际 {tier2['unit_price']}")
        
        if not sum_ok:
            tr21_ok = False
            tr21_detail.append(f"breakdown 加总不等于 amount: {sum_val:.2f} ≠ {result['amount']:.2f}")
        
        results['TR-2.1'] = (tr21_ok, result, tr21_detail)
        print(f"  结果: {'✅ PASS' if tr21_ok else '❌ FAIL'}")
        for d in tr21_detail:
            print(f"    - {d}")
        print()
        
        # ============================================================
        # TR-2.2: water 15 吨
        # ============================================================
        print("-" * 70)
        print("TR-2.2: water 15 吨")
        print("预期: 档1 0-12吨@3.5, 档2 12吨以上@4.6, 加总 = amount")
        print("-" * 70)
        result = calculate_tiered_amount("water", 15)
        print(f"  返回 amount = {result['amount']:.2f}")
        print_breakdown(result['breakdown'])
        sum_ok, sum_val = verify_sum(result)
        print(f"  breakdown 加总验证: {sum_val:.2f} {'=' if sum_ok else '≠'} {result['amount']:.2f} -> {'PASS' if sum_ok else 'FAIL'}")
        
        # 预期手动计算: tier1=12*3.5=42, tier2=3*4.6=13.8, total=55.8
        expected_tier1_usage = 12
        expected_tier1_subtotal = 12 * 3.5
        expected_tier2_usage = 3
        expected_tier2_subtotal = 3 * 4.6
        expected_total = 55.80
        
        tr22_ok = True
        tr22_detail = []
        
        tier1 = next((b for b in result['breakdown'] if b['tier'] == 1), None)
        tier2 = next((b for b in result['breakdown'] if b['tier'] == 2), None)
        
        if tier1 is None:
            tr22_ok = False
            tr22_detail.append("缺少 tier1")
        else:
            if abs(tier1['usage_in_tier'] - expected_tier1_usage) > 0.001:
                tr22_ok = False
                tr22_detail.append(f"tier1 用量错误: 预期 {expected_tier1_usage}, 实际 {tier1['usage_in_tier']}")
            if abs(tier1['subtotal'] - expected_tier1_subtotal) > 0.001:
                tr22_ok = False
                tr22_detail.append(f"tier1 subtotal 错误: 预期 {expected_tier1_subtotal:.2f}, 实际 {tier1['subtotal']:.2f}")
            if abs(tier1['unit_price'] - 3.5) > 0.0001:
                tr22_ok = False
                tr22_detail.append(f"tier1 单价错误: 预期 3.5, 实际 {tier1['unit_price']}")
        
        if tier2 is None:
            tr22_ok = False
            tr22_detail.append("缺少 tier2")
        else:
            if abs(tier2['usage_in_tier'] - expected_tier2_usage) > 0.001:
                tr22_ok = False
                tr22_detail.append(f"tier2 用量错误: 预期 {expected_tier2_usage}, 实际 {tier2['usage_in_tier']}")
            if abs(tier2['subtotal'] - expected_tier2_subtotal) > 0.001:
                tr22_ok = False
                tr22_detail.append(f"tier2 subtotal 错误: 预期 {expected_tier2_subtotal:.2f}, 实际 {tier2['subtotal']:.2f}")
            if abs(tier2['unit_price'] - 4.6) > 0.0001:
                tr22_ok = False
                tr22_detail.append(f"tier2 单价错误: 预期 4.6, 实际 {tier2['unit_price']}")
        
        if abs(result['amount'] - expected_total) > 0.001:
            tr22_ok = False
            tr22_detail.append(f"amount 错误: 预期 {expected_total:.2f}, 实际 {result['amount']:.2f}")
        
        if not sum_ok:
            tr22_ok = False
            tr22_detail.append(f"breakdown 加总不等于 amount: {sum_val:.2f} ≠ {result['amount']:.2f}")
        
        results['TR-2.2'] = (tr22_ok, result, tr22_detail)
        print(f"  结果: {'✅ PASS' if tr22_ok else '❌ FAIL'}")
        for d in tr22_detail:
            print(f"    - {d}")
        print()
        
        # ============================================================
        # TR-2.3: gas 350 立方
        # ============================================================
        print("-" * 70)
        print("TR-2.3: gas 350 立方")
        print("预期: 档1 0-310@2.67, 档2 310-600@2.95, 加总 = amount")
        print("-" * 70)
        result = calculate_tiered_amount("gas", 350)
        print(f"  返回 amount = {result['amount']:.2f}")
        print_breakdown(result['breakdown'])
        sum_ok, sum_val = verify_sum(result)
        print(f"  breakdown 加总验证: {sum_val:.2f} {'=' if sum_ok else '≠'} {result['amount']:.2f} -> {'PASS' if sum_ok else 'FAIL'}")
        
        expected_tier1_usage = 310
        expected_tier1_subtotal = 310 * 2.67
        expected_tier2_usage = 40
        expected_tier2_subtotal = 40 * 2.95
        expected_total = float((Decimal(str(expected_tier1_subtotal)) + Decimal(str(expected_tier2_subtotal))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        
        tr23_ok = True
        tr23_detail = []
        
        tier1 = next((b for b in result['breakdown'] if b['tier'] == 1), None)
        tier2 = next((b for b in result['breakdown'] if b['tier'] == 2), None)
        
        if tier1 is None:
            tr23_ok = False
            tr23_detail.append("缺少 tier1")
        else:
            if abs(tier1['usage_in_tier'] - expected_tier1_usage) > 0.001:
                tr23_ok = False
                tr23_detail.append(f"tier1 用量错误: 预期 {expected_tier1_usage}, 实际 {tier1['usage_in_tier']}")
            if abs(tier1['subtotal'] - expected_tier1_subtotal) > 0.001:
                tr23_ok = False
                tr23_detail.append(f"tier1 subtotal 错误: 预期 {expected_tier1_subtotal:.2f}, 实际 {tier1['subtotal']:.2f}")
            if abs(tier1['unit_price'] - 2.67) > 0.0001:
                tr23_ok = False
                tr23_detail.append(f"tier1 单价错误: 预期 2.67, 实际 {tier1['unit_price']}")
        
        if tier2 is None:
            tr23_ok = False
            tr23_detail.append("缺少 tier2")
        else:
            if abs(tier2['usage_in_tier'] - expected_tier2_usage) > 0.001:
                tr23_ok = False
                tr23_detail.append(f"tier2 用量错误: 预期 {expected_tier2_usage}, 实际 {tier2['usage_in_tier']}")
            if abs(tier2['subtotal'] - expected_tier2_subtotal) > 0.001:
                tr23_ok = False
                tr23_detail.append(f"tier2 subtotal 错误: 预期 {expected_tier2_subtotal:.2f}, 实际 {tier2['subtotal']:.2f}")
            if abs(tier2['unit_price'] - 2.95) > 0.0001:
                tr23_ok = False
                tr23_detail.append(f"tier2 单价错误: 预期 2.95, 实际 {tier2['unit_price']}")
        
        if abs(result['amount'] - expected_total) > 0.001:
            tr23_ok = False
            tr23_detail.append(f"amount 错误: 预期 {expected_total:.2f}, 实际 {result['amount']:.2f}")
        
        if not sum_ok:
            tr23_ok = False
            tr23_detail.append(f"breakdown 加总不等于 amount: {sum_val:.2f} ≠ {result['amount']:.2f}")
        
        results['TR-2.3'] = (tr23_ok, result, tr23_detail)
        print(f"  结果: {'✅ PASS' if tr23_ok else '❌ FAIL'}")
        for d in tr23_detail:
            print(f"    - {d}")
        print()
        
        # ============================================================
        # TR-2.4: 任意 type 用量 0
        # ============================================================
        print("-" * 70)
        print("TR-2.4: 任意 type 用量 0 -> amount=0.0, breakdown=[]")
        print("-" * 70)
        tr24_ok = True
        tr24_detail = []
        for type_ in ["electricity", "water", "gas"]:
            result = calculate_tiered_amount(type_, 0)
            print(f"  {type_}: amount={result['amount']}, breakdown={result['breakdown']}")
            if result['amount'] != 0.0:
                tr24_ok = False
                tr24_detail.append(f"{type_}: amount 错误: 预期 0.0, 实际 {result['amount']}")
            if result['breakdown'] != []:
                tr24_ok = False
                tr24_detail.append(f"{type_}: breakdown 错误: 预期 [], 实际 {result['breakdown']}")
        
        results['TR-2.4'] = (tr24_ok, None, tr24_detail)
        print(f"  结果: {'✅ PASS' if tr24_ok else '❌ FAIL'}")
        for d in tr24_detail:
            print(f"    - {d}")
        print()
        
        # ============================================================
        # TR-2.5: electricity 500 度 (超出档2上限)
        # ============================================================
        print("-" * 70)
        print("TR-2.5: electricity 500 度 (超出档2上限400的100度按档3@0.888)")
        print("预期: tier1=180@0.588, tier2=220@0.638, tier3=100@0.888")
        print("-" * 70)
        result = calculate_tiered_amount("electricity", 500)
        print(f"  返回 amount = {result['amount']:.2f}")
        print_breakdown(result['breakdown'])
        sum_ok, sum_val = verify_sum(result)
        print(f"  breakdown 加总验证: {sum_val:.2f} {'=' if sum_ok else '≠'} {result['amount']:.2f} -> {'PASS' if sum_ok else 'FAIL'}")
        
        expected_tier1_usage = 180
        expected_tier1_subtotal = 180 * 0.588
        expected_tier2_usage = 220
        expected_tier2_subtotal = 220 * 0.638
        expected_tier3_usage = 100
        expected_tier3_subtotal = 100 * 0.888
        expected_total = float((Decimal(str(expected_tier1_subtotal)) + Decimal(str(expected_tier2_subtotal)) + Decimal(str(expected_tier3_subtotal))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        
        tr25_ok = True
        tr25_detail = []
        
        tier1 = next((b for b in result['breakdown'] if b['tier'] == 1), None)
        tier2 = next((b for b in result['breakdown'] if b['tier'] == 2), None)
        tier3 = next((b for b in result['breakdown'] if b['tier'] == 3), None)
        
        if tier1 is None:
            tr25_ok = False
            tr25_detail.append("缺少 tier1")
        else:
            if abs(tier1['usage_in_tier'] - expected_tier1_usage) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier1 用量错误: 预期 {expected_tier1_usage}, 实际 {tier1['usage_in_tier']}")
            if abs(tier1['subtotal'] - expected_tier1_subtotal) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier1 subtotal 错误: 预期 {expected_tier1_subtotal:.2f}, 实际 {tier1['subtotal']:.2f}")
        
        if tier2 is None:
            tr25_ok = False
            tr25_detail.append("缺少 tier2")
        else:
            if abs(tier2['usage_in_tier'] - expected_tier2_usage) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier2 用量错误: 预期 {expected_tier2_usage}, 实际 {tier2['usage_in_tier']}")
            if abs(tier2['subtotal'] - expected_tier2_subtotal) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier2 subtotal 错误: 预期 {expected_tier2_subtotal:.2f}, 实际 {tier2['subtotal']:.2f}")
        
        if tier3 is None:
            tr25_ok = False
            tr25_detail.append("缺少 tier3 (超出档2上限的用量未进入档3)")
        else:
            if abs(tier3['usage_in_tier'] - expected_tier3_usage) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier3 用量错误: 预期 {expected_tier3_usage}, 实际 {tier3['usage_in_tier']}")
            if abs(tier3['subtotal'] - expected_tier3_subtotal) > 0.001:
                tr25_ok = False
                tr25_detail.append(f"tier3 subtotal 错误: 预期 {expected_tier3_subtotal:.2f}, 实际 {tier3['subtotal']:.2f}")
            if abs(tier3['unit_price'] - 0.888) > 0.0001:
                tr25_ok = False
                tr25_detail.append(f"tier3 单价错误: 预期 0.888, 实际 {tier3['unit_price']}")
        
        if abs(result['amount'] - expected_total) > 0.001:
            tr25_ok = False
            tr25_detail.append(f"amount 错误: 预期 {expected_total:.2f}, 实际 {result['amount']:.2f}")
        
        if not sum_ok:
            tr25_ok = False
            tr25_detail.append(f"breakdown 加总不等于 amount: {sum_val:.2f} ≠ {result['amount']:.2f}")
        
        results['TR-2.5'] = (tr25_ok, result, tr25_detail)
        print(f"  结果: {'✅ PASS' if tr25_ok else '❌ FAIL'}")
        for d in tr25_detail:
            print(f"    - {d}")
        print()
        
        # ============================================================
        # 汇总
        # ============================================================
        print("=" * 70)
        print("汇总结果")
        print("=" * 70)
        all_pass = True
        for key, (ok, result, detail) in results.items():
            status = "✅ PASS" if ok else "❌ FAIL"
            if not ok:
                all_pass = False
            if result is not None and 'breakdown' in result:
                amount_info = f"amount={result['amount']:.2f}"
            elif key == 'TR-2.4':
                amount_info = "amount=0, breakdown=[]"
            else:
                amount_info = ""
            print(f"  {key}: {status} {amount_info}")
        print()
        if all_pass:
            print("🎉 全部测试通过!")
        else:
            print("⚠️  存在失败的测试用例，需要修复 billing.py")
        
        return results


if __name__ == "__main__":
    run_tests()
