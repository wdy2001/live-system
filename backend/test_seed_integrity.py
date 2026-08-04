"""种子数据完整性测试脚本 + 阶梯金额手工验算
用法: USE_SQLITE=true python test_seed_integrity.py
"""
import os
import sys

os.environ.setdefault("USE_SQLITE", "true")

from app import create_app
from extensions import db
from models import (
    User, Household, Meter, BillTypeRule, Bill, Payment, RepairRequest,
)
from services.billing import calculate_tiered_amount


PASS = 0
FAIL = 0
FAILURES = []


def check(name, condition, extra=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        msg = f"  FAIL: {name}"
        if extra:
            msg += f" | {extra}"
        print(msg)
        FAILURES.append((name, extra))


def main():
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 70)
        print("  SEED DATA INTEGRITY TESTS")
        print("=" * 70)

        # ---------- a) users ----------
        print("\n[a] users 表校验")
        users = User.query.all()
        check("users 计数 = 2", len(users) == 2, f"实际={len(users)}")

        demo_user = User.query.filter_by(username="demo").first()
        admin_user = User.query.filter_by(username="admin").first()
        check("存在 username=demo", demo_user is not None)
        check("存在 username=admin", admin_user is not None)
        check("demo.role == user", demo_user and demo_user.role == "user",
              f"实际={demo_user.role if demo_user else None}")
        check("admin.role == admin", admin_user and admin_user.role == "admin",
              f"实际={admin_user.role if admin_user else None}")
        check("demo.password_hash 非空", demo_user and bool(demo_user.password_hash))
        check("admin.password_hash 非空", admin_user and bool(admin_user.password_hash))
        check("demo password_hash 不以明文 demo123 开头",
              demo_user and not demo_user.password_hash.startswith("demo123"),
              f"hash前10={demo_user.password_hash[:10] if demo_user else ''}")
        check("admin password_hash 不以明文 admin123 开头",
              admin_user and not admin_user.password_hash.startswith("admin123"),
              f"hash前10={admin_user.password_hash[:10] if admin_user else ''}")

        # ---------- b) households ----------
        print("\n[b] households 表校验")
        households = Household.query.all()
        check("households 计数 = 1", len(households) == 1, f"实际={len(households)}")
        h1 = households[0] if households else None
        check("household 关联 user_id == demo.id",
              h1 and demo_user and h1.user_id == demo_user.id,
              f"h1.user_id={h1.user_id if h1 else None}, demo.id={demo_user.id if demo_user else None}")
        check("household_no 非空", h1 and bool(h1.household_no),
              f"household_no={h1.household_no if h1 else None}")
        check("address 非空", h1 and bool(h1.address),
              f"address={h1.address if h1 else None}")

        # ---------- c) meters ----------
        print("\n[c] meters 表校验")
        meters = Meter.query.all()
        check("meters 计数 = 3", len(meters) == 3, f"实际={len(meters)}")
        meter_types = {m.type for m in meters}
        check("meter type 集合 == {electricity,water,gas}",
              meter_types == {"electricity", "water", "gas"},
              f"实际={meter_types}")
        for m in meters:
            check(f"meter[{m.type}] meter_no 非空", bool(m.meter_no),
                  f"meter_no={m.meter_no}")

        # ---------- d) bill_type_rules ----------
        print("\n[d] bill_type_rules 表校验")
        rules = BillTypeRule.query.all()
        check("bill_type_rules 计数 = 8", len(rules) == 8, f"实际={len(rules)}")
        elec_rules = sorted([r for r in rules if r.type == "electricity"], key=lambda r: r.tier)
        water_rules = sorted([r for r in rules if r.type == "water"], key=lambda r: r.tier)
        gas_rules = sorted([r for r in rules if r.type == "gas"], key=lambda r: r.tier)
        check("electricity 规则 = 3 条", len(elec_rules) == 3, f"实际={len(elec_rules)}")
        check("water 规则 = 2 条", len(water_rules) == 2, f"实际={len(water_rules)}")
        check("gas 规则 = 3 条", len(gas_rules) == 3, f"实际={len(gas_rules)}")

        check("electricity tier 连续 1,2,3",
              [r.tier for r in elec_rules] == [1, 2, 3],
              f"实际={[r.tier for r in elec_rules]}")
        check("water tier 连续 1,2",
              [r.tier for r in water_rules] == [1, 2],
              f"实际={[r.tier for r in water_rules]}")
        check("gas tier 连续 1,2,3",
              [r.tier for r in gas_rules] == [1, 2, 3],
              f"实际={[r.tier for r in gas_rules]}")

        if elec_rules:
            check("electricity tier1 min=0", float(elec_rules[0].min_usage) == 0.0,
                  f"实际={elec_rules[0].min_usage}")
            check("electricity tier1 max=180", float(elec_rules[0].max_usage) == 180.0,
                  f"实际={elec_rules[0].max_usage}")
            check("electricity tier1 unit_price=0.588", float(elec_rules[0].unit_price) == 0.588,
                  f"实际={elec_rules[0].unit_price}")

        # ---------- e) bills ----------
        print("\n[e] bills 表校验")
        bills = Bill.query.all()
        check("bills 计数 = 18", len(bills) == 18, f"实际={len(bills)}")
        periods = sorted({b.period for b in bills})
        check("period 覆盖 6 个连续月份", len(periods) == 6,
              f"periods={periods}")

        from datetime import datetime
        def add_one_month(dt):
            total_months = dt.year * 12 + (dt.month - 1)
            total_months += 1
            y, m0 = divmod(total_months, 12)
            return dt.replace(year=y, month=m0 + 1)
        period_dates = [datetime.strptime(p, "%Y-%m") for p in periods]
        period_dates_sorted = sorted(period_dates)
        consecutive = True
        for i in range(1, len(period_dates_sorted)):
            expected = add_one_month(period_dates_sorted[i - 1])
            if expected != period_dates_sorted[i]:
                consecutive = False
                break
        check("period 从 oldest→newest 连续", consecutive,
              f"sorted periods={[p.strftime('%Y-%m') for p in period_dates_sorted]}")

        paid_bills = [b for b in bills if b.status == "paid"]
        unpaid_bills = [b for b in bills if b.status == "unpaid"]
        check("paid 账单数 = 12 (4月×3类)", len(paid_bills) == 12,
              f"实际 paid={len(paid_bills)}, unpaid={len(unpaid_bills)}")
        check("unpaid 账单数 = 6 (2月×3类)", len(unpaid_bills) == 6,
              f"实际 paid={len(paid_bills)}, unpaid={len(unpaid_bills)}")

        paid_periods = sorted({b.period for b in paid_bills})
        unpaid_periods = sorted({b.period for b in unpaid_bills})
        check("paid period < 2026-04",
              all(p < "2026-04" for p in paid_periods),
              f"paid periods={paid_periods}")
        check("unpaid period >= 2026-04",
              all(p >= "2026-04" for p in unpaid_periods),
              f"unpaid periods={unpaid_periods}")

        # ---------- f) payments ----------
        print("\n[f] payments 表校验")
        payments = Payment.query.all()
        check("payments 计数 = 12", len(payments) == 12, f"实际={len(payments)}")
        paid_bill_ids = {b.id for b in paid_bills}
        payment_bill_ids = {p.bill_id for p in payments}
        check("每条 payment.bill_id 对应一张 paid bill",
              payment_bill_ids == paid_bill_ids,
              f"payment bill_ids={sorted(payment_bill_ids)}, paid bill_ids={sorted(paid_bill_ids)}")
        for p in payments:
            bill = Bill.query.get(p.bill_id)
            check(f"payment[{p.id}] amount == bill.amount",
                  bill and float(p.amount) == float(bill.amount),
                  f"payment.amount={p.amount}, bill.amount={bill.amount if bill else None}")

        # ---------- g) repair_requests ----------
        print("\n[g] repair_requests 表校验")
        repairs = RepairRequest.query.all()
        check("repair_requests 计数 = 3", len(repairs) == 3, f"实际={len(repairs)}")
        repair_statuses = {r.status for r in repairs}
        check("status 集合 == {pending,processing,resolved}",
              repair_statuses == {"pending", "processing", "resolved"},
              f"实际={repair_statuses}")
        urgent_count = sum(1 for r in repairs if r.urgency == "urgent")
        check("至少 1 条 urgency='urgent'", urgent_count >= 1,
              f"实际 urgent={urgent_count}")

        # ---------- 4. 阶梯金额手工验算 ----------
        print("\n" + "=" * 70)
        print("  TIERED AMOUNT CALCULATION VERIFICATION")
        print("=" * 70)

        # electricity: usage=250, expected=150.50
        # 180 * 0.588 = 105.84
        # 70 * 0.638 = 44.66
        # Total = 150.50
        print("\n[h] electricity usage=250 → 预期 150.50")
        elec_result = calculate_tiered_amount("electricity", 250)
        elec_amount = elec_result.get("amount")
        print(f"    计算结果: {elec_amount}, breakdown: {elec_result.get('breakdown')}")
        check("electricity 250度 == 150.50",
              abs(elec_amount - 150.50) < 0.001,
              f"实际={elec_amount}")

        # water: usage=15, expected=55.80
        # 12 * 3.5 = 42
        # 3 * 4.6 = 13.8
        # Total = 55.80
        print("\n[i] water usage=15 → 预期 55.80")
        water_result = calculate_tiered_amount("water", 15)
        water_amount = water_result.get("amount")
        print(f"    计算结果: {water_amount}, breakdown: {water_result.get('breakdown')}")
        check("water 15吨 == 55.80",
              abs(water_amount - 55.80) < 0.001,
              f"实际={water_amount}")

        # gas: usage=45, expected=120.15
        # 45 * 2.67 = 120.15
        print("\n[j] gas usage=45 → 预期 120.15")
        gas_result = calculate_tiered_amount("gas", 45)
        gas_amount = gas_result.get("amount")
        print(f"    计算结果: {gas_amount}, breakdown: {gas_result.get('breakdown')}")
        check("gas 45立方 == 120.15",
              abs(gas_amount - 120.15) < 0.001,
              f"实际={gas_amount}")

        # ---------- 汇总 ----------
        print("\n" + "=" * 70)
        print(f"  SUMMARY: PASS={PASS} / FAIL={FAIL}")
        print("=" * 70)
        if FAILURES:
            print("  失败用例:")
            for idx, (name, extra) in enumerate(FAILURES, 1):
                line = f"    {idx}. {name}"
                if extra:
                    line += f" | {extra}"
                print(line)
        print()

        return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
