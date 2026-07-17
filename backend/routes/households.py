"""户号路由"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User, Household, Meter

households_bp = Blueprint("households", __name__)


@households_bp.get("/mine")
@jwt_required()
def my_households():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify(msg="用户不存在"), 404

    households = Household.query.filter_by(user_id=uid).all()
    result = []
    for h in households:
        d = h.to_dict()
        d["meters"] = [m.to_dict() for m in h.meters]
        result.append(d)
    return jsonify(households=result)
