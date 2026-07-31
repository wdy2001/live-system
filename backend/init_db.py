import sys
import os
import logging
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("init_db")

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import engine, SessionLocal, Base
from app import models  # noqa: F401 - ensure all models are registered with Base
from app.models import BillingRule, MeterUsage, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    logger.info("开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")


def seed_billing_rules(db):
    count = db.execute(text("SELECT COUNT(*) FROM billing_rules")).scalar()
    if count and count > 0:
        logger.info(f"billing_rules 表已有 {count} 条记录，跳过种子数据")
        return

    logger.info("开始写入 billing_rules 种子计费规则...")

    rules = [
        BillingRule(type="electric", tier_min=Decimal("0"), tier_max=Decimal("180"),
                    unit_price=Decimal("0.5200"), extra_fee_name="政府性基金及附加",
                    extra_fee_rate=Decimal("0.0500"), description="电费第一阶梯"),
        BillingRule(type="electric", tier_min=Decimal("181"), tier_max=Decimal("280"),
                    unit_price=Decimal("0.5700"), extra_fee_name="政府性基金及附加",
                    extra_fee_rate=Decimal("0.0500"), description="电费第二阶梯"),
        BillingRule(type="electric", tier_min=Decimal("281"), tier_max=None,
                    unit_price=Decimal("0.8700"), extra_fee_name="政府性基金及附加",
                    extra_fee_rate=Decimal("0.0500"), description="电费第三阶梯"),

        BillingRule(type="water", tier_min=Decimal("0"), tier_max=Decimal("15"),
                    unit_price=Decimal("2.9000"), extra_fee_name="污水处理费",
                    extra_fee_rate=Decimal("1.2000"), description="水费第一阶梯"),
        BillingRule(type="water", tier_min=Decimal("16"), tier_max=Decimal("25"),
                    unit_price=Decimal("4.3000"), extra_fee_name="污水处理费",
                    extra_fee_rate=Decimal("1.2000"), description="水费第二阶梯"),
        BillingRule(type="water", tier_min=Decimal("26"), tier_max=None,
                    unit_price=Decimal("7.0000"), extra_fee_name="污水处理费",
                    extra_fee_rate=Decimal("1.2000"), description="水费第三阶梯"),

        BillingRule(type="gas", tier_min=Decimal("0"), tier_max=Decimal("310"),
                    unit_price=Decimal("2.6300"), extra_fee_name="燃气附加费",
                    extra_fee_rate=Decimal("0.1500"), description="燃气费第一阶梯"),
        BillingRule(type="gas", tier_min=Decimal("311"), tier_max=Decimal("500"),
                    unit_price=Decimal("3.1500"), extra_fee_name="燃气附加费",
                    extra_fee_rate=Decimal("0.1500"), description="燃气费第二阶梯"),
        BillingRule(type="gas", tier_min=Decimal("501"), tier_max=None,
                    unit_price=Decimal("3.9200"), extra_fee_name="燃气附加费",
                    extra_fee_rate=Decimal("0.1500"), description="燃气费第三阶梯"),
    ]

    db.add_all(rules)
    db.commit()
    logger.info(f"billing_rules 种子数据写入完成，共 {len(rules)} 条")


def seed_meter_usages(db):
    count = db.execute(text("SELECT COUNT(*) FROM meter_usages")).scalar()
    if count and count > 0:
        logger.info(f"meter_usages 表已有 {count} 条记录，跳过种子数据")
        return

    current_month = datetime.utcnow().strftime("%Y-%m")
    logger.info(f"开始写入 meter_usages 示例用量数据，月份: {current_month}...")

    usages = [
        MeterUsage(house_no="E100001", type="electric", month=current_month,
                   usage_amount=Decimal("350.00")),
        MeterUsage(house_no="W200002", type="water", month=current_month,
                   usage_amount=Decimal("18.00")),
        MeterUsage(house_no="G300003", type="gas", month=current_month,
                   usage_amount=Decimal("380.00")),
    ]

    db.add_all(usages)
    db.commit()
    logger.info(f"meter_usages 种子数据写入完成，共 {len(usages)} 条")


def seed_demo_user(db):
    count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    if count and count > 0:
        logger.info(f"users 表已有 {count} 条记录，跳过演示用户创建")
        return

    logger.info("开始创建演示用户 (demo / demo123456)...")
    hashed = pwd_context.hash("demo123456")
    demo_user = User(
        username="demo",
        password_hash=hashed,
        full_name="演示用户",
        phone="13800138000",
        address="示例地址",
    )
    db.add(demo_user)
    db.commit()
    logger.info("演示用户创建完成")


def main():
    logger.info("===== 数据库初始化开始 =====")

    create_tables()

    db = SessionLocal()
    try:
        seed_billing_rules(db)
        seed_meter_usages(db)
        seed_demo_user(db)
    finally:
        db.close()

    logger.info("初始化完成")


if __name__ == "__main__":
    main()
