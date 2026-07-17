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
            password_hash=generate_password_hash("admin123"),
            real_name="系统管理员",
            phone="13800000000",
            role="admin",
        )
        demo = User(
            username="demo",
            password_hash=generate_password_hash("demo123"),
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
            # 水价：两档
            BillTypeRule(type="water", tier=1, min_usage=0, max_usage=12, unit_price=3.5000, description="第一档（月用水 0-12 吨）"),
            BillTypeRule(type="water", tier=2, min_usage=12, max_usage=None, unit_price=4.6000, description="第二档（月用水 12 吨以上）"),
            # 气价：两档
            BillTypeRule(type="gas", tier=1, min_usage=0, max_usage=310, unit_price=2.6700, description="第一档（年用气 0-310 立方）"),
            BillTypeRule(type="gas", tier=2, min_usage=310, max_usage=600, unit_price=2.9500, description="第二档（年用气 311-600 立方）"),
            BillTypeRule(type="gas", tier=3, min_usage=600, max_usage=None, unit_price=3.5600, description="第三档（年用气 600 立方以上）"),
        ]
        db.session.add_all(rules)
        db.session.commit()

        # ---------- 账单（近 6 个月 + 本月未缴） ----------
        now = datetime.utcnow()
        bill_rows = [
            # period, type, prev, curr
            ("2025-12", "electricity", 2580, 2680),
            ("2025-12", "water", 430, 442),
            ("2025-12", "gas", 180, 195),
            ("2026-01", "electricity", 2680, 2805),
            ("2026-01", "water", 442, 455),
            ("2026-01", "gas", 195, 208),
            ("2026-02", "electricity", 2805, 2920),
            ("2026-02", "water", 455, 468),
            ("2026-02", "gas", 208, 220),
            ("2026-03", "electricity", 2920, 3020),
            ("2026-03", "water", 468, 478),
            ("2026-03", "gas", 220, 230),
            ("2026-04", "electricity", 3020, 3080),
            ("2026-04", "water", 478, 486),
            ("2026-04", "gas", 230, 243),
            ("2026-05", "electricity", 3080, 3120),
            ("2026-05", "water", 486, 498),
            ("2026-05", "gas", 243, 256),
        ]
        meter_map = {m.type: m for m in meters}
        for period, btype, prev, curr in bill_rows:
            usage = curr - prev
            amount = _calc(rules, btype, usage)
            # 近两个月未缴，更早的已缴
            is_paid = period < "2026-04"
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
                paid_at=datetime.utcnow() - timedelta(days=10) if is_paid else None,
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
                user_id=demo.id, type="electricity", description="客厅灯经常闪烁，疑似线路接触不良",
                phone="13900001111", urgency="normal", status="resolved",
                created_at=datetime.utcnow() - timedelta(days=20),
                resolved_at=datetime.utcnow() - timedelta(days=15),
            ),
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
