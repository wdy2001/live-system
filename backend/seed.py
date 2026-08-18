"""种子数据脚本：创建表 + 写入演示数据

用法:
    cd backend
    python seed.py
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import (
    User, Household, Meter, BillTypeRule, Bill, Payment, RepairRequest,
)


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 清空旧数据
        for model in (Payment, Bill, Meter, Household, BillTypeRule, RepairRequest, User):
            model.query.delete()
        db.session.commit()

        # ---------- 用户 ----------
        admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123", method="pbkdf2:sha256"),
            real_name="系统管理员",
            phone="13800000000",
            role="admin",
        )
        demo = User(
            username="demo",
            password_hash=generate_password_hash("demo123", method="pbkdf2:sha256"),
            real_name="张小明",
            phone="13900001111",
            role="user",
        )
        db.session.add_all([admin, demo])
        db.session.commit()

        # ---------- 户号与表计 ----------
        h1 = Household(user_id=demo.id, household_no="HH20240001", address="阳光花园 3 栋 2 单元 501")
        db.session.add(h1)
        db.session.commit()

        meters = [
            Meter(household_id=h1.id, type="electricity", meter_no="EL-0001", current_reading=3120),
            Meter(household_id=h1.id, type="water", meter_no="WT-0001", current_reading=486),
            Meter(household_id=h1.id, type="gas", meter_no="GS-0001", current_reading=215),
        ]
        db.session.add_all(meters)
        db.session.commit()

        # ---------- 计费规则（阶梯） ----------
        rules = [
            # 电价：三档
            BillTypeRule(type="electricity", tier=1, min_usage=0, max_usage=180, unit_price=0.5880, description="第一档（年用电 0-180 度）"),
            BillTypeRule(type="electricity", tier=2, min_usage=180, max_usage=400, unit_price=0.6380, description="第二档（年用电 181-400 度）"),
            BillTypeRule(type="electricity", tier=3, min_usage=400, max_usage=None, unit_price=0.8880, description="第三档（年用电 400 度以上）"),
            # 水价：三档
            BillTypeRule(type="water", tier=1, min_usage=0, max_usage=12, unit_price=3.5000, description="第一档（月用水 0-12 吨）"),
            BillTypeRule(type="water", tier=2, min_usage=12, max_usage=24, unit_price=4.6000, description="第二档（月用水 13-24 吨）"),
            BillTypeRule(type="water", tier=3, min_usage=24, max_usage=None, unit_price=5.8000, description="第三档（月用水 24 吨以上）"),
            # 气价：三档
            BillTypeRule(type="gas", tier=1, min_usage=0, max_usage=310, unit_price=2.6800, description="第一档（年用气 0-310 立方）"),
            BillTypeRule(type="gas", tier=2, min_usage=310, max_usage=600, unit_price=2.9100, description="第二档（年用气 311-600 立方）"),
            BillTypeRule(type="gas", tier=3, min_usage=600, max_usage=None, unit_price=3.5600, description="第三档（年用气 600 立方以上）"),
        ]
        db.session.add_all(rules)
        db.session.commit()

        # ---------- 账单（近 6 个月 + 最近 2 个月未缴） ----------
        now = datetime.utcnow()
        # 动态生成近 6 个月的账单周期：以当前月份为基准向前推 5 个月（共 6 个月）
        # 例如：当前 2026-08 → 周期为 2026-03, 2026-04, 2026-05, 2026-06, 2026-07, 2026-08
        # 状态规则：前 4 个月（较早）已缴，最近 2 个月未缴
        periods = []
        for i in range(5, -1, -1):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            periods.append(f"{y:04d}-{m:02d}")

        # 动态生成读数：以 meters 中 current_reading 为终点，向前反推每月读数
        # 每月增量（与原硬编码一致）：电 60/125/115/100/60/40，水 12/13/13/10/8/12，气 15/13/12/10/13/13
        # 简化：固定每月增量（按顺序，索引 0 是最早月份）
        type_monthly_increments = {
            "electricity": [100, 125, 115, 100, 60, 40],
            "water":       [12,  13,  13,  10,  8,  12],
            "gas":         [15,  13,  12,  10,  13,  13],
        }
        meter_map = {m.type: m for m in meters}
        bill_rows = []
        for btype in ("electricity", "water", "gas"):
            increments = type_monthly_increments[btype]
            curr = float(meter_map[btype].current_reading)
            readings_backward = []
            for inc in reversed(increments):
                prev = curr - inc
                readings_backward.append((prev, curr))
                curr = prev
            # readings_backward 顺序：[ (month5_prev, month5_curr), ..., (month0_prev, month0_curr) ]
            # 翻转使其与 periods 对齐（索引 0 最早月份）
            readings = list(reversed(readings_backward))
            for i, period in enumerate(periods):
                prev_r, curr_r = readings[i]
                bill_rows.append((period, btype, prev_r, curr_r))

        # 最近 2 个月未缴（periods 最后 2 个），更早的已缴
        unpaid_start_idx = len(periods) - 2
        unpaid_periods = set(periods[unpaid_start_idx:])
        for period, btype, prev, curr in bill_rows:
            usage = curr - prev
            amount = _calc(rules, btype, usage)
            is_paid = period not in unpaid_periods
            bill = Bill(
                household_id=h1.id,
                meter_id=meter_map[btype].id,
                type=btype,
                period=period,
                previous_reading=prev,
                current_reading=curr,
                usage_amount=usage,
                amount=amount,
                status="paid" if is_paid else "unpaid",
                paid_at=datetime.utcnow() - timedelta(days=10 + (len(periods) - periods.index(period))) if is_paid else None,
            )
            db.session.add(bill)
            db.session.flush()
            if is_paid:
                db.session.add(Payment(
                    bill_id=bill.id,
                    amount=amount,
                    method="alipay",
                    transaction_no=f"PAY{period.replace('-','')}{btype[:2].upper()}001",
                    paid_at=bill.paid_at,
                ))
        db.session.commit()

        # ---------- 报修工单 ----------
        repairs = [
            RepairRequest(
                user_id=demo.id, type="water", description="厨房水龙头漏水，关不紧",
                phone="13900001111", urgency="normal", status="processing",
                created_at=datetime.utcnow() - timedelta(days=3),
            ),
            RepairRequest(
                user_id=demo.id, type="gas", description="燃气灶打不着火，需要检修",
                phone="13900001111", urgency="urgent", status="pending",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
        ]
        db.session.add_all(repairs)
        db.session.commit()

        print("✅ 种子数据写入完成")
        print("   演示账号: demo / demo123")
        print("   管理员账号: admin / admin123")


def _calc(rules, btype, usage):
    """简易阶梯计算（与 services.billing 等价，用于种子）"""
    from decimal import Decimal, ROUND_HALF_UP
    type_rules = sorted([r for r in rules if r.type == btype], key=lambda r: r.tier)
    remaining = Decimal(str(usage))
    total = Decimal("0")
    for r in type_rules:
        if remaining <= 0:
            break
        cap = (Decimal(str(r.max_usage)) - Decimal(str(r.min_usage))) if r.max_usage is not None else remaining
        used = min(remaining, cap)
        total += used * Decimal(str(r.unit_price))
        remaining -= used
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


if __name__ == "__main__":
    seed()
