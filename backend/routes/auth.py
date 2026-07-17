"""认证路由：注册 / 登录 / 当前用户"""
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User

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
