"""认证路由：注册 / 登录 / 当前用户"""
import random
import string
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User, Household, Meter

auth_bp = Blueprint("auth", __name__)


def _generate_household_no(user_id: int) -> str:
    """生成唯一户号: HH{yyyyMMdd}{4位随机} 或 U{uid} 保证唯一"""
    date_str = datetime.now().strftime("%Y%m%d")
    for _ in range(100):
        rand4 = ''.join(random.choices(string.digits, k=4))
        hh_no = f"HH{date_str}{rand4}"
        if not Household.query.filter_by(household_no=hh_no).first():
            return hh_no
    fallback = f"U{user_id}"
    while Household.query.filter_by(household_no=fallback).first():
        user_id += 1
        fallback = f"U{user_id}"
    return fallback


def _generate_meter_no(prefix: str) -> str:
    """生成唯一表号: {prefix}-{rand8}"""
    for _ in range(100):
        rand8 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        meter_no = f"{prefix}-{rand8}"
        if not Meter.query.filter_by(meter_no=meter_no).first():
            return meter_no
    suffix = 1000
    while True:
        meter_no = f"{prefix}-{suffix}"
        if not Meter.query.filter_by(meter_no=meter_no).first():
            return meter_no
        suffix += 1


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password")
    real_name = (data.get("real_name") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not username or not password:
        return jsonify(msg="用户名和密码不能为空"), 400
    if len(username) < 4 or len(username) > 20:
        return jsonify(msg="用户名长度需为 4-20 位"), 400
    if len(password) < 6 or len(password) > 20:
        return jsonify(msg="密码长度需为 6-20 位"), 400
    if confirm_password is not None and confirm_password != password:
        return jsonify(msg="两次输入的密码不一致"), 400
    if User.query.filter_by(username=username).first():
        return jsonify(msg="用户名已存在"), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name or username,
        phone=phone,
        role="user",
    )
    db.session.add(user)
    db.session.flush()

    household_no = _generate_household_no(user.id)
    household = Household(
        user_id=user.id,
        household_no=household_no,
        address="",
    )
    db.session.add(household)
    db.session.flush()

    meter_prefix_map = {
        "electricity": "EL",
        "water": "WT",
        "gas": "GS",
    }
    for meter_type, prefix in meter_prefix_map.items():
        meter_no = _generate_meter_no(prefix)
        meter = Meter(
            household_id=household.id,
            type=meter_type,
            meter_no=meter_no,
            current_reading=0,
        )
        db.session.add(meter)

    db.session.commit()

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
