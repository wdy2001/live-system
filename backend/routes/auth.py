"""认证路由：注册 / 登录 / 当前用户"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User, Household, Meter, BillTypeRule

auth_bp = Blueprint("auth", __name__)


def _ensure_default_rules():
    """确保阶梯计费规则表有默认数据（如为空则写入）"""
    if BillTypeRule.query.first() is not None:
        return
    defaults = [
        # 电价三档
        BillTypeRule(type="electricity", tier=1, min_usage=0, max_usage=180, unit_price=0.5880, description="第一档（月用电 0-180 度）"),
        BillTypeRule(type="electricity", tier=2, min_usage=180, max_usage=400, unit_price=0.6380, description="第二档（月用电 181-400 度）"),
        BillTypeRule(type="electricity", tier=3, min_usage=400, max_usage=None, unit_price=0.8880, description="第三档（月用电 400 度以上）"),
        # 水价三档
        BillTypeRule(type="water", tier=1, min_usage=0, max_usage=15, unit_price=3.5000, description="第一档（月用水 0-15 吨）"),
        BillTypeRule(type="water", tier=2, min_usage=15, max_usage=25, unit_price=4.8000, description="第二档（月用水 16-25 吨）"),
        BillTypeRule(type="water", tier=3, min_usage=25, max_usage=None, unit_price=6.5000, description="第三档（月用水 25 吨以上）"),
        # 气价三档
        BillTypeRule(type="gas", tier=1, min_usage=0, max_usage=30, unit_price=2.6300, description="第一档（月用气 0-30 立方）"),
        BillTypeRule(type="gas", tier=2, min_usage=30, max_usage=50, unit_price=3.1500, description="第二档（月用气 31-50 立方）"),
        BillTypeRule(type="gas", tier=3, min_usage=50, max_usage=None, unit_price=3.9500, description="第三档（月用气 50 立方以上）"),
    ]
    db.session.add_all(defaults)
    db.session.commit()


def _create_household_for_user(user_id: int):
    """为新用户创建默认户号 + 电/水/气 3 块表"""
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    household_no = f"HH{now}{user_id:04d}"
    household = Household(user_id=user_id, household_no=household_no, address=f"用户 #{user_id} 默认户号")
    db.session.add(household)
    db.session.flush()
    meters = [
        Meter(household_id=household.id, type="electricity", meter_no=f"EL{now}{user_id:03d}", current_reading=0),
        Meter(household_id=household.id, type="water", meter_no=f"WT{now}{user_id:03d}", current_reading=0),
        Meter(household_id=household.id, type="gas", meter_no=f"GS{now}{user_id:03d}", current_reading=0),
    ]
    db.session.add_all(meters)
    db.session.commit()


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    real_name = (data.get("real_name") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not username or not password:
        return jsonify(msg="用户名和密码不能为空"), 400
    if len(password) < 6:
        return jsonify(msg="密码长度至少 6 位"), 400
    if User.query.filter_by(username=username).first():
        return jsonify(msg="用户名已存在"), 409

    _ensure_default_rules()

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name or username,
        phone=phone,
        role="user",
    )
    db.session.add(user)
    db.session.commit()

    _create_household_for_user(user.id)

    token = create_access_token(identity=str(user.id))
    return jsonify(token=token, user=user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(msg="用户名或密码错误"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(token=token, user=user.to_dict())


@auth_bp.get("/me")
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify(msg="用户不存在"), 404
    return jsonify(user=user.to_dict())
