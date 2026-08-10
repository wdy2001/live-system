"""故障报修路由"""
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, RepairRequest

repairs_bp = Blueprint("repairs", __name__)

PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")
VALID_TYPES = {"electricity", "water", "gas", "other"}
VALID_URGENCIES = {"normal", "urgent"}
VALID_STATUSES = {"pending", "processing", "resolved"}


@repairs_bp.get("")
@jwt_required()
def list_repairs():
    uid = int(get_jwt_identity())
    status = request.args.get("status")
    query = RepairRequest.query.filter_by(user_id=uid)
    if status and status in VALID_STATUSES:
        query = query.filter_by(status=status)
    repairs = query.order_by(RepairRequest.created_at.desc()).all()
    return jsonify(repairs=[r.to_dict() for r in repairs])


@repairs_bp.post("")
@jwt_required()
def create_repair():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify(msg="用户不存在"), 404

    data = request.get_json() or {}
    rtype = data.get("type")
    description = (data.get("description") or "").strip()
    phone = (data.get("phone") or "").strip()
    urgency = data.get("urgency", "normal")

    if rtype not in VALID_TYPES:
        return jsonify(msg="报修类型无效"), 400

    desc_len = len(description)
    if desc_len < 10 or desc_len > 500:
        return jsonify(msg="故障描述长度需为 10-500 字"), 400

    if not PHONE_REGEX.match(phone):
        return jsonify(msg="联系电话格式错误"), 400

    if urgency not in VALID_URGENCIES:
        urgency = "normal"

    repair = RepairRequest(
        user_id=uid,
        type=rtype,
        description=description,
        phone=phone,
        urgency=urgency,
        status="pending",
    )
    db.session.add(repair)
    db.session.commit()
    return jsonify(repair=repair.to_dict()), 201


@repairs_bp.get("/<int:repair_id>")
@jwt_required()
def repair_detail(repair_id):
    uid = int(get_jwt_identity())
    repair = RepairRequest.query.get(repair_id)
    if not repair:
        return jsonify(msg="工单不存在"), 404
    if repair.user_id != uid:
        return jsonify(msg="无权访问该工单"), 403
    return jsonify(repair=repair.to_dict())
