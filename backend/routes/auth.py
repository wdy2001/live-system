"""认证路由：注册 / 登录 / 当前用户"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User, Household, Meter

auth_bp = Blueprint("auth", __name__)


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

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name or username,
        phone=phone,
        role="user",
    )
    db.session.add(user)
    db.session.flush()

    date_str = datetime.now().strftime("%Y%m%d")
    household = Household(
        user_id=user.id,
        household_no=f"HH{date_str}{user.id}",
        address="默认地址（请在户号管理中完善）",
    )
    db.session.add(household)
    db.session.flush()

    user_id_padded = str(user.id).zfill(6)
    meter_types = [
        ("electricity", f"EL-{user_id_padded}"),
        ("water", f"WT-{user_id_padded}"),
        ("gas", f"GS-{user_id_padded}"),
    ]
    for mtype, mno in meter_types:
        meter = Meter(
            household_id=household.id,
            type=mtype,
            meter_no=mno,
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
